package com.kh.back.taste.dto;

import java.util.List;
import java.util.Map;

public record TasteCatalogResponse(long versionId, int version, int questionCount, Map<String, Type> types,
                           List<Question> questions, List<Branch> rules) {
    public record Type(long id, String name, String description, List<String> tags, List<Vehicle> vehicles) {}
    public record Vehicle(long id, String name, String category, String image) {}
    public record Option(long id, String text, Map<String, Integer> weights) {}
    public record Question(String id, long databaseId, int step, String title, boolean initial, List<Option> options) {}
    public record Branch(String sourceId, Long optionId, String nextId, String leadingType) {}
}
