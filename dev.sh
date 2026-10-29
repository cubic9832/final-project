#!/usr/bin/env bash
# 개발 환경 한 번에 실행: MySQL(Docker) + Spring Boot + Vite
#   ./dev.sh         전체 실행 (Ctrl+C 로 back/front 종료, DB 컨테이너는 유지)
#   ./dev.sh down    DB 컨테이너 중지 (데이터 유지)
#   ./dev.sh reset   DB 컨테이너와 데이터 삭제 (다음 실행 때 Flyway 가 처음부터 적용)
#   DB_PORT=3308 ./dev.sh   기본 3307 대신 다른 포트를 쓸 때
# Windows 는 Git Bash 없이 dev.cmd 를 사용한다.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

DEFAULT_DB_PORT=3307
export DB_PORT="${DB_PORT:-$DEFAULT_DB_PORT}"

require_docker() {
  if ! docker info >/dev/null 2>&1; then
    echo "Docker 가 실행 중이 아닙니다. Docker Desktop 을 켠 뒤 다시 실행하세요." >&2
    exit 1
  fi
}

is_db_running() {
  [ -n "$(docker compose ps -q --status running db 2>/dev/null)" ]
}

is_port_in_use() {
  (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null
}

start_db() {
  if ! is_db_running && is_port_in_use "$DB_PORT"; then
    echo "$DB_PORT 포트를 다른 프로세스가 사용 중입니다. 예: DB_PORT=3308 ./dev.sh" >&2
    exit 1
  fi
  docker compose up -d --wait db
}

lan_ipv4_windows() {
  powershell.exe -NoProfile -Command '
    $addresses = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {
      $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" -and
      $_.InterfaceAlias -notmatch "vEthernet|WSL|Hyper-V|Loopback|Bluetooth|Virtual|Docker|Default Switch"
    })
    $ethernet = @($addresses | Where-Object { $_.InterfaceAlias -match "Ethernet|이더넷" })
    if ($ethernet.Count -gt 0) { $ethernet[0].IPAddress; exit }
    $wifi = @($addresses | Where-Object { $_.InterfaceAlias -match "Wi-Fi|WiFi|Wireless|WLAN|무선" })
    if ($wifi.Count -gt 0) { $wifi[0].IPAddress; exit }
    if ($addresses.Count -gt 0) { $addresses[0].IPAddress }
  ' | tr -d "\r"
}

lan_ipv4_darwin() {
  local iface ip
  if command -v networksetup >/dev/null 2>&1; then
    while IFS= read -r iface; do
      [ -n "$iface" ] || continue
      ip="$(ipconfig getifaddr "$iface" 2>/dev/null || true)"
      if [ -n "$ip" ]; then
        printf "%s\n" "$ip"
        return 0
      fi
    done < <(networksetup -listallhardwareports 2>/dev/null | awk '
      /^Hardware Port: / {
        port = substr($0, 16)
        kind = ""
        if (port ~ /Ethernet/ && port !~ /Bridge/) kind = "ethernet"
        else if (port == "Wi-Fi") kind = "wifi"
        getline
        if (kind != "" && $1 == "Device:") {
          if (kind == "ethernet") ethernet[++n] = $2
          else wifi = $2
        }
      }
      END {
        for (i = 1; i <= n; i++) print ethernet[i]
        if (wifi != "") print wifi
      }
    ')
  fi
  iface="$(route -n get default 2>/dev/null | awk "/interface:/{print \$2}")"
  if [ -n "${iface:-}" ]; then
    ipconfig getifaddr "$iface" 2>/dev/null || true
  fi
}

lan_ipv4_linux() {
  ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i <= NF; i++) if ($i == "src") { print $(i + 1); exit }}'
}

lan_ipv4() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) lan_ipv4_windows ;;
    Darwin) lan_ipv4_darwin ;;
    *) lan_ipv4_linux ;;
  esac
}

print_lan_access() {
  local ip
  ip="$(lan_ipv4 || true)"
  if [ -z "$ip" ]; then
    echo "같은 네트워크 IP를 찾지 못했습니다. ipconfig에서 이더넷 IPv4를 확인하세요."
    return
  fi
  echo "같은 네트워크 IPv4: $ip"
  echo "다른 PC 프론트: http://$ip:5173"
  echo "다른 PC DB 확인 (cmd, mysql 클라이언트 필요):"
  echo "mysql -h $ip -P $DB_PORT -u server -pserver final_sample -e \"SELECT MAX(version) v, MIN(success) ok FROM flyway_schema_history; SELECT status, COUNT(*) c FROM managed_vehicles GROUP BY status;\""
  echo "기대값: v=20, ok=1, PUBLISHED=308, REVIEW=3"
}

APP_PIDS=()

stop_apps() {
  trap - INT TERM EXIT
  echo
  echo "back/front 를 종료합니다. (DB 컨테이너는 유지: ./dev.sh down 으로 중지)"
  kill "${APP_PIDS[@]}" 2>/dev/null || true
  wait 2>/dev/null || true
}

start_apps() {
  if [ "$DB_PORT" != "$DEFAULT_DB_PORT" ]; then
    export SPRING_DATASOURCE_URL="jdbc:mysql://localhost:$DB_PORT/final_sample?serverTimezone=Asia/Seoul&characterEncoding=UTF-8"
  fi

  print_lan_access

  if [ ! -d front/node_modules ]; then
    (cd front && npm ci)
  fi

  trap stop_apps INT TERM EXIT

  # 소스 저장 시 재컴파일 → spring-boot-devtools 가 서버를 자동 재시작
  (cd back && exec ./gradlew classes --continuous --quiet) &
  APP_PIDS+=($!)
  (cd back && exec ./gradlew bootRun) &
  APP_PIDS+=($!)
  (cd front && exec npm run dev) &
  APP_PIDS+=($!)

  echo "front: http://localhost:5173  /  back: http://localhost:8080"
  wait
}

case "${1:-up}" in
  up)
    require_docker
    start_db
    start_apps
    ;;
  down)
    require_docker
    docker compose stop db
    ;;
  reset)
    require_docker
    docker compose down -v
    ;;
  *)
    echo "사용법: ./dev.sh [up|down|reset]" >&2
    exit 1
    ;;
esac
