import { useRef, useState } from 'react';
import { reorderPriorities } from './reorderPriorities';

export default function VehiclePriorities({ priorities, onChange }) {
  const gesture = useRef(null);
  const [drag, setDrag] = useState(null);
  const [announcement, setAnnouncement] = useState('');

  function move(source, target) {
    const reordered = reorderPriorities(priorities, source, target);
    if (reordered === priorities) return;
    onChange(reordered);
    setAnnouncement(`${source}, ${reordered.indexOf(source) + 1}순위로 이동했습니다.`);
  }

  function startDrag(event, item) {
    if (!event.isPrimary || event.button !== 0) return;
    const rect = event.currentTarget.getBoundingClientRect();
    gesture.current = { source: item, target: null, x: event.clientX, y: event.clientY, offsetX: event.clientX - rect.left, offsetY: event.clientY - rect.top, width: rect.width, height: rect.height, moved: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function updateDrag(event) {
    const current = gesture.current;
    if (!current) return;
    if (!current.moved && Math.hypot(event.clientX - current.x, event.clientY - current.y) < 5) return;
    current.moved = true;
    const list = event.currentTarget.closest('ol');
    const bounds = list.getBoundingClientRect();
    current.target = null;
    if (event.clientX >= bounds.left - 12 && event.clientX <= bounds.right + 12 && event.clientY >= bounds.top - 12 && event.clientY <= bounds.bottom + 12) {
      const candidates = [...list.querySelectorAll('[data-vehicle-priority]')]
        .filter((element) => element.dataset.vehiclePriority !== current.source)
        .map((element) => {
          const rect = element.getBoundingClientRect();
          const dx = Math.max(rect.left - event.clientX, 0, event.clientX - rect.right);
          const dy = Math.max(rect.top - event.clientY, 0, event.clientY - rect.bottom);
          return { element, rect, distance: Math.hypot(dx, dy) };
        }).sort((a, b) => a.distance - b.distance);
      const nearest = candidates[0];
      if (nearest) {
        current.target = nearest.element.dataset.vehiclePriority;
        current.after = event.clientX > nearest.rect.left + nearest.rect.width / 2;
      }
    }
    setDrag({ source: current.source, target: current.target, after: current.after,
      left: event.clientX - current.offsetX, top: event.clientY - current.offsetY, width: current.width, height: current.height });
  }

  function finishDrag(event) {
    const current = gesture.current;
    if (current?.moved && current.target) {
      const reordered = priorities.filter((item) => item !== current.source);
      const insertion = reordered.indexOf(current.target) + (current.after ? 1 : 0);
      reordered.splice(insertion, 0, current.source);
      onChange(reordered);
      setAnnouncement(`${current.source}, ${insertion + 1}순위로 이동했습니다.`);
    }
    gesture.current = null;
    setDrag(null);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
  }

  function cancelDrag() {
    gesture.current = null;
    setDrag(null);
  }

  return (
    <section className="vehicle-priorities" aria-labelledby="vehicle-priorities-title">
      <h3 id="vehicle-priorities-title">중요조건 우선순위</h3>
      <p id="vehicle-priorities-help">드래그하여 순서를 바꿀 수 있습니다. 키보드에서는 항목을 선택하고 방향키를 사용하세요.</p>
      <ol aria-label="중요조건 우선순위">
        {priorities.map((item, index) => (
          <li key={item} className={drag?.target === item ? `vehicle-insert-${drag.after ? 'after' : 'before'}` : undefined}>
            <button
              type="button"
              data-vehicle-priority={item}
              className={`vehicle-priority${drag?.source === item ? ' dragging' : ''}`}
              aria-label={`${index + 1}순위 ${item}`}
              aria-describedby="vehicle-priorities-help"
              onPointerDown={(event) => startDrag(event, item)}
              onPointerMove={updateDrag}
              onPointerUp={finishDrag}
              onPointerCancel={cancelDrag}
              onLostPointerCapture={cancelDrag}
              onKeyDown={(event) => {
                if (event.key === 'Escape') { cancelDrag(); return; }
                const direction = ['ArrowLeft', 'ArrowUp'].includes(event.key) ? -1 : ['ArrowRight', 'ArrowDown'].includes(event.key) ? 1 : 0;
                if (!direction) return;
                event.preventDefault();
                if (priorities[index + direction]) move(item, priorities[index + direction]);
              }}
            >
              <span className="vehicle-drag-handle" aria-hidden="true">⠿</span>
              <span>{index + 1} {item}</span>
            </button>
          </li>
        ))}
      </ol>
      {drag && (
        <div className="vehicle-priority vehicle-drag-preview" aria-hidden="true"
          style={{ left: drag.left, top: drag.top, width: drag.width, height: drag.height }}>
          <span className="vehicle-drag-handle">⠿</span>
          <span>{priorities.indexOf(drag.source) + 1} {drag.source}</span>
        </div>
      )}
      <span className="vehicle-sr-only" role="status">{announcement}</span>
    </section>
  );
}
