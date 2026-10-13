# 프로필 캐릭터 이미지

내장 image_gen 도구로 생성한 투명 배경 이미지 5종이다. 공통 프롬프트의 `{subject}`를 아래 각 내용으로 대체했고 `transparent_background: true`를 사용했다.

## 공통 프롬프트

Use case: illustration-story. Asset: small profile card character illustration for a Korean financial automobile comparison website. Subject: {subject} Style: restrained cohesive 2D flat editorial character illustration, rounded simple geometric forms, minimal dot eyes and tiny smile, dark navy hair, warm neutral skin, solid color fills, no gradients, no texture, no realism, no 3D, no shadows. Palette: navy #203960, mint #54B19D, light blue #ECF3FC, off-white. Full body composition centered in a square canvas, entire figure including shoes and all objects visible, generous 10 percent transparent margin around subject, characters occupy 80 percent canvas height. Adult proportions softly simplified (head about one quarter of height), readable at 120px height. True transparent background. No scenery, no ground, no text, no letters, no logo, no watermark. This is one of five coordinated illustrations; maintain identical visual language.

## 이미지별 Subject

- `starter.webp`: One young adult in casual mint commuting clothes holding a small navy shoulder bag.
- `employee.webp`: One office employee in a neat light blue shirt with a plain blank mint employee badge on a navy lanyard.
- `couple.webp`: Two adult working partners standing side by side, different neat commuting outfits, one mint jacket and one light blue shirt, carrying small work bags.
- `family.webp`: A family of two parents and one small child standing together, the child between the adults, warm simple expressions.
- `freelancer.webp`: One casually dressed freelancer sitting cross-legged using an open navy laptop on their lap, mint sweatshirt.


## 웹 최적화

배포 자산은 512×512 WebP로 변환했다. cwebp 품질 85, 압축 노력 6, 알파 품질 100을 적용하고 메타데이터를 제거했다. 생성 원본 PNG는 Codex 생성 이미지 폴더에 보존한다.
