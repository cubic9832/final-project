package com.kh.back.auth;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 중복 확인 응답 (보완 3): { "available": true } = 사용할 수 있음, false = 이미 사용 중
 */
@Getter
@AllArgsConstructor
public class AvailabilityResponse {

    private final boolean available;
}
