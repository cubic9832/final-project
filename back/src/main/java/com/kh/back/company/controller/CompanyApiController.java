package com.kh.back.company.controller;

import com.kh.back.common.dto.ApiResponse;
import com.kh.back.common.dto.PageMeta;
import com.kh.back.company.dto.CompanyDto;
import com.kh.back.company.service.CompanyService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController // 반환값을 화면 이름이 아니라 JSON 으로 응답
@RequestMapping("/api/v1/companies")
@RequiredArgsConstructor
public class CompanyApiController {

    private final CompanyService companyService;

    // GET /api/v1/companies?page=1&size=20
    @GetMapping
    public ApiResponse<List<CompanyDto>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        page = Math.max(page, 1);
        size = Math.min(Math.max(size, 1), 100); // 한 번에 최대 100건

        List<CompanyDto> companies = companyService.getCompanies(page, size);
        int total = companyService.countCompanies();
        return ApiResponse.ok(companies, PageMeta.of(page, size, total));
    }

    // GET /api/v1/companies/G0001
    @GetMapping("/{code}")
    public ApiResponse<CompanyDto> detail(@PathVariable String code) {
        return ApiResponse.ok(companyService.getCompany(code));
    }
}
