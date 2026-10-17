# 사용자 결정과 근거 대응표 — 2026-10-17
기계 판독 원본: `data/research/coaching/reviews/scenario-evidence-map-20261017.json`.
기존 자료를 참조하여 중복 전사하지 않는다. 이번 결과는 내부 조사 데이터이며 공개 처방이 아니다.

| ID | 사용자 질문 | 연결 근거 | 현재 공백 |
|---|---|---|---|
| SD01 | SBD 자세를 모르면 무엇부터 하나? | nsca_deadlift, nsca_squat, mao2023, petrizzo2018 | Bench instructional source; reviewed video/cues; practice-to-training transition |
| SD02 | 1RM 없이 첫 중량을 어떻게 고르나? | petrizzo2018, self_selection, learning_trial, acsm2026 | Unsupervised starting procedure and product applicability |
| SD03 | 언제 얼마를 증량하나? | petrizzo2018, mao2023, acsm2026 | Numeric increment not supplied by Petrizzo; cannot invent it as source fact |
| SD04 | 목표 반복을 못 채우면? | mao2023, helms2018, autoreg2022 | Applicability of source-specific adjustments outside original programme |
| SD05 | 감량한 오늘 운동은 의미가 있나? | mao2023, helms2018, autoreg2022 | No individual causal benefit estimate for arbitrary reduction |
| SD06 | 휴식을 줄이거나 늘리면? | rest2016, rest2010, mao2023 | Different populations/protocols; no universal per-second penalty |
| SD07 | 힘듦/RIR 입력을 얼마나 신뢰하나? | rir_accuracy, helms2018, metd2021 | Measurement validation review pending, especially novices |
| SD08 | 훈련량을 늘리면 정체를 풀 수 있나? | volume2019, acsm2026, per2018 | No validated personal plateau threshold or automatic add-set rule |
| SD09 | SBD에 맞는 주간 구성을 어떻게 고르나? | metd2021, per2018, helms2018, zourdos2016, autoreg2022 | Applicability/release review; Helms incomplete SBD |
| SD10 | 휴식기/결석 후 어떻게 복귀하나? | deload2024, acsm2026 | No reviewed gap-to-load formula |
| SD11 | 통증/자세/장비 사유가 다르면? | 기존 제품 경계 | Clinical guidance not reviewed; source-specific reduction cannot resolve pain |
| SD12 | 연구와 내 성장 차트를 어떻게 비교하나? | mao2023, helms2018, metd2021, rest2010 | User-vs-group causal comparison invalid |

## 이번에 실제로 추가한 것
- 12개 결정 질문, 17개 근거 참조(기술 교육2건 포함), 질문별 필요한 입력·공백·다음 작업.
- 원문 조정 조건2건과 휴식 해석 검토1건을 구조화. 실행 규칙으로 활성화하지 않음.
- 기존 추출본과 Mao 원문 Methods2.3/2.5 대조: familiarization/감독/반복 미달 후 다음 세트 감량 확인.
- Gentil2010 초록에서 초보 남성 휴식 비교의 군간 비유의 결과와 차트용 보고값 추출.
- 보고된 ± 값의 종류를 초록에서 확인하지 못했으므로 SD로 단정하거나 오차막대에 사용하지 않음.
- rest2016 기존 검토와 반대 방향의 결과도 연결. 대상/휴식 정의/훈련량 차이로 바로 모순 판정하지 않음.
- NSCA deadlift 공식 페이지 확인. 영상 자체 검토/번역/재사용 허가 완료 아님.
- PubMed 일부 페이지는 본문이 반환되지 않아 검색 후보 상태로 유지. 원문 검토했다고 표시하지 않음.

## 적대적 검토 결과
1. 근거가 있는 방법과 그 방법의 독립 효과를 분리한다. Mao의 감량은 연구 내 절차이지 감량 대 중단 무작위 비교가 아니다.
2. Petrizzo의 참여자 선택 증량 폭을 고정 kg 규칙으로 꾸미지 않는다.
3. 초보 휴식 연구의 비유의 결과를 동등성 입증으로 바꾸지 않는다.
4. 연구와 메타분석을 독립 표본처럼 합산하지 않는다. 코호트 중복 확인 전 근거 개수 점수 금지.
5. 루틴 공급 공백은 유지된다. 이 파일 적재를 숙련별 루틴 제공 완료로 보고하지 않는다.

## 바로 이어질 구현 입력
우선 SD01/SD02/SD03: SBD 교육의 벤치 공백, 첫 부하 선택, 전 세트 완료 이후 진행.
다음 SD04/SD05/SD06: 기존 원장 기반 조건 대조와 종료 설명.
SD09의 기존 프로그램은 삭제/재작성하지 않고 적합성 검토로 연결한다.
이번 파일은 런타임 loader에 연결하지 않는다. 기존 공개/내부 실행 경계를 변경하지 않는다.

## 다음 다섯 검토 질문
1. 입문 교육에서 벤치/스쿼트/데드리프트 각각 어느 동작 설명과 도움 경로가 확보됐는가?
2. 감독 없는 첫 부하 선택에서 연구 사실과 제품 적용 판단은 어디서 나뉘는가?
3. 감량 방법을 연구에서 사용했다는 사실을 효과 입증으로 잘못 설명하지 않는가?
4. 휴식 연구의 대상·훈련량·비교 조건 차이를 응답에서 구분하는가?
5. 어떤 근거 공백이 공개를 막고, 어떤 공백은 기록·설명을 유지하며 안내할 수 있는가?
