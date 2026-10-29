package com.kh.back.chatbot.util;

import java.util.regex.Pattern;

public final class PiiMasker {
    private static final Pattern RRN = Pattern.compile("(?<!\\d)\\d{6}\\s?-?\\s?[1-8]\\d{6}(?!\\d)");
    private static final Pattern CARD = Pattern.compile("(?<!\\d)(?:\\d{4}([- ])\\d{4}\\1\\d{4}\\1\\d{4}|\\d{13,19})(?!\\d)");
    private static final Pattern PHONE = Pattern.compile("(?<!\\d)0(?:1[016789]|2|[3-6]\\d)[ -]?\\d{3,4}[ -]?\\d{4}(?!\\d)");
    private static final Pattern ACCOUNT = Pattern.compile("(?<!\\d)\\d{2,6}-\\d{2,6}-\\d{4,8}(?!\\d)");
    private static final Pattern EMAIL = Pattern.compile("[\\w.+-]+@[\\w-]+(?:\\.[\\w-]+)+");
    private PiiMasker() {}
    public static String mask(String text) {
        if (text == null) return "";
        String result = RRN.matcher(text).replaceAll("[주민번호]");
        result = CARD.matcher(result).replaceAll("[카드번호]");
        result = PHONE.matcher(result).replaceAll("[전화번호]");
        result = ACCOUNT.matcher(result).replaceAll("[계좌번호]");
        return EMAIL.matcher(result).replaceAll("[이메일]");
    }
}
