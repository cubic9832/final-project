package com.kh.back.chatbot.service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.stereotype.Component;

/** Small local lexical RAG index. Korean bigrams also match words with particles. */
@Component
public class ChatKnowledge {
    public record Chunk(String id, String title, String text, Set<String> terms) {}
    private final List<Chunk> chunks;

    public ChatKnowledge(@Value("${chatbot.knowledge-location:classpath:chatbot/knowledge/*.md}") String location) throws IOException {
        var loaded = new ArrayList<Chunk>();
        var resources = new PathMatchingResourcePatternResolver().getResources(location);
        Arrays.sort(resources, Comparator.comparing(resource -> Objects.toString(resource.getFilename(), "")));
        for (var resource : resources) {
            String text = resource.getContentAsString(StandardCharsets.UTF_8);
            String filename = Objects.toString(resource.getFilename(), "document");
            int index = 0;
            for (String section : text.split("(?m)(?=^## )")) {
                if (section.isBlank()) continue;
                String title = section.lines().findFirst().orElse(filename).replaceFirst("^#+\\s*", "");
                for (int start = 0; start < section.length(); start += 1000) {
                    String part = section.substring(start, Math.min(start + 1200, section.length()));
                    loaded.add(new Chunk(filename + "#" + (++index), title, part, terms(title + " " + part)));
                }
            }
        }
        chunks = List.copyOf(loaded);
    }

    public List<Chunk> search(String question) {
        Set<String> query = terms(question);
        var scores = new HashMap<Chunk, Double>();
        for (var chunk : chunks) {
            double score = 0;
            for (String term : query) {
                if (!chunk.terms().contains(term)) continue;
                long frequency = chunks.stream().filter(item -> item.terms().contains(term)).count();
                score += Math.log(1 + (double) chunks.size() / frequency);
            }
            if (score > 0) scores.put(chunk, score / Math.sqrt(Math.max(1, chunk.terms().size())));
        }
        return scores.keySet().stream()
                .sorted(Comparator.<Chunk>comparingDouble(scores::get).reversed().thenComparing(Chunk::id))
                .limit(4).toList();
    }

    private static Set<String> terms(String text) {
        var result = new HashSet<String>();
        for (String word : text.toLowerCase(Locale.ROOT).split("[^\\p{L}\\p{N}]+")) {
            if (word.isEmpty()) continue;
            result.add(word);
            if (word.matches("[가-힣]+")) {
                for (int i = 0; i < word.length() - 1; i++) result.add(word.substring(i, i + 2));
            }
        }
        return result;
    }
}
