# 공식 이미지에 한국어 형태소 분석기(nori)를 설치한다. 버전은 docker-compose.yml 의 ES_VERSION 과 같다.
ARG ES_VERSION
FROM docker.elastic.co/elasticsearch/elasticsearch:${ES_VERSION}
RUN bin/elasticsearch-plugin install --batch analysis-nori
