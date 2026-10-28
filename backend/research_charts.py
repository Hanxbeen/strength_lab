"""Finite, audited research chart projections, never personal forecasts.

Numbers are transcribed from the specified primary-source locations.
No network requests, graph digitization, interpolation, or inferred post-tests.
Every call builds a fresh payload; callers cannot mutate shared chart state.
"""

HELMS_SHA = "1ec02777c1ea7ef63393384d14ee6270dfd45cd6412f7c2e32f795f292498b12"
METD_SHA = "ec922473ddd0107354830afe5d0ae545b3e6f964fe7b98f3cdaf9f2b4e326bf6"
PER_XML_SHA = "d3b91266b5f34e143d1c0864c2d33473b440dd789dd19c1e847f3c39a4b79bb1"
PETRIZZO_SHA = "fc8eb398f4a9eac7318eb3e22a3c2ea751cde935e22fe76633d013a4fb64b152"
PER_DEFINITION_SHA = "386ab9b07fc2a68a48d3105f314d19e5d2229d8fb34a47025e4687c6fcdd092d"
COMMON_LIMIT = "연구 결과는 개인의 예상 성장량·목표선·운동 효과 달성률이 아니에요."

def _base(source, arm):
    return dict(schema_version="research-chart-v1", available=False,
        reason="reviewed_outcome_data_unavailable", selected_arm=arm,
        source={"definition_id": source.get("id"), "url": None,
                "locator": None, "source_sha256": None, "attribution": None,
                "license": None},
        population=None, timepoint=None, metric=None, unit=None,
        statistic=None, chart_kind=None, points=[], limits=[COMMON_LIMIT],
        scientific_approval=False, individual_forecast=False,
        interpolation_allowed=False, user_comparison_allowed=False)

def _unavailable(result, reason, explanation):
    result.update(available=False, reason=reason, points=[])
    result["limits"].append(explanation)
    return result

def chart_for(source, arm=None):
    """Return a chart contract for a reviewed source and its selected arm.

    Group comparisons retain *all* reported groups. Study 3/4 in METD must
    be rendered separately (panel_id); they are not a four-arm trial.
    """
    result = _base(source, arm)
    identity = source.get("id", "")
    if identity == "10.3389/fphys.2018.00247":
        result["source"].update(url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5877330/",
            locator="Abstract / Results (change scores); Table 1 (completer counts)",
            source_sha256=HELMS_SHA, attribution="Helms et al. (2018), Frontiers in Physiology 9:247",
            license="CC BY")
        if source.get("source_sha256") != HELMS_SHA:
            return _unavailable(result, "source_revision_unreviewed", "원문 버전이 달라 수치를 표시하지 않아요.")
        if arm not in (None, "1RMG", "RPEG"):
            return _unavailable(result, "arm_not_reviewed", "이 선택안과 연결한 결과가 없어요.")
        result.update(available=True, reason=None, metric="measured_1rm_change",
            unit="kg", statistic="mean_change_with_standard_deviation",
            chart_kind="group_change_with_sd", population={
                "description": "저항훈련 경험이 있는 남성, 완료자 21명",
                "design": "strength_counterbalanced_parallel_groups_not_randomized",
                "started": 24, "analyzed": 21, "groups": {"1RMG": 11, "RPEG": 10}},
            timepoint={"baseline_week": 0, "post_week": 8})
        for exercise, values in (
            ("barbell_back_squat", ((13.91, 5.89), (17.05, 5.44))),
            ("barbell_bench_press", ((9.64, 5.36), (10.70, 3.30))),
            ("squat_bench_combined_total", ((23.55, 10.38), (27.75, 7.94)))):
            for group, (value, sd) in zip(("1RMG", "RPEG"), values):
                result["points"].append(dict(panel_id=exercise, exercise_id=exercise,
                    arm=group, n=11 if group=="1RMG" else 10, value=value,
                    sd=sd, unit="kg", selected=group==arm))
        result["limits"] += [
            "두 군 모두 증가했지만 군 간 차이는 통계적으로 유의하지 않았어요. 동등하다는 증명은 아니에요.",
            "오차 막대는 변화량의 표준편차이며 개인의 예상 범위나 신뢰구간이 아니에요.",
            "초록의 변화량을 사용해요. 본문의 1RMG 벤치 사후값은 변화량과 일치하지 않아 전후값을 재구성하지 않아요.",
            "데드리프트 결과는 없어요. 중간 주차 측정값이나 개인 성장곡선을 만들지 않아요."]
        return result
    if identity == "metd2021-sbd-v1":
        result["source"].update(url="https://pmc.ncbi.nlm.nih.gov/articles/PMC8435792/",
            locator="Studies 3 and 4 / Results (sec44); Table 8",
            source_sha256=METD_SHA,
            attribution="Androulakis-Korakakis et al. (2021), Frontiers in Sports and Active Living 3:713655",
            license="CC BY")
        if source.get("citation", {}).get("source_sha256") != METD_SHA:
            return _unavailable(result, "source_revision_unreviewed", "원문 버전이 달라 수치를 표시하지 않아요.")
        if arm not in (None, "MAX", "MAX_BOFF", "AMRAP"):
            return _unavailable(result, "arm_not_reviewed", "이 선택안과 연결한 결과가 없어요.")
        result.update(available=True, reason=None, metric="sbd_total_1rm_change",
            unit="kg", statistic="posterior_mode_with_95_percent_hdi",
            chart_kind="separate_study_interval_panels",
            population={"description":"파워리프팅 경험이 있는 남성, 연구 3 완료자 16명·연구 4 완료자 9명",
                "design":"two_quasi_randomized_small_training_studies",
                "studies": {"3":{"MAX":8,"MAX_BOFF":8}, "4":{"MAX_BOFF":5,"AMRAP":4}}},
            timepoint={"training_weeks":6,"pre_days_before_training":7,"post_days_after_training":5})
        for study, group, n, value, lower, upper in (
            (3,"MAX",8,11.4,0.8,19.5), (3,"MAX_BOFF",8,33.7,24.3,44.1),
            (4,"MAX_BOFF",5,26.8,17.3,41.6), (4,"AMRAP",4,15.3,3.4,31.3)):
            result["points"].append(dict(panel_id="study_"+str(study), study=study,
                arm=group,n=n,value=value,unit="kg",interval_lower=lower,
                interval_upper=upper,interval_kind="95_percent_hdi",
                selected=group==arm,prior_from_study_3=(study==4 and group=="MAX_BOFF")))
        result["limits"] += [
            "수치는 관측 평균이 아닌 베이지안 사후분포의 최빈값이며 범위는 95% HDI예요.",
            "연구 3과 4를 별도 패널로 표시해요. 네 군을 한 실험의 순위로 비교하지 않아요.",
            "연구 4 MAX+back-off 분석에는 연구 3의 사전정보가 반영됐어요.",
            "표 12의 설문 자기보고 및 의미 있는 증가량에 대한 설문을 실험 결과와 섞지 않아요.",
            "작은 표본의 추정치예요. 개인 성공 확률이나 종목별 효과로 환산하지 않아요."]
        return result
    if identity == "pilot2018-per-source-labels-v1":
        result["source"].update(url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6162635/",
            locator="Table 4 / sports-06-00086-t004 (SBD rows only)",
            source_sha256=PER_XML_SHA,
            attribution="Androulakis-Korakakis et al. (2018), Sports 6(3):86",
            license="CC-BY-4.0")
        if source.get("source_sha256") != PER_DEFINITION_SHA:
            return _unavailable(result, "source_revision_unreviewed", "원 정의의 버전이 달라 수치를 표시하지 않아요.")
        if arm not in (None, "PER_SOURCE_LABELS"):
            return _unavailable(result, "arm_not_reviewed", "이 선택안과 연결한 결과가 없어요.")
        result.update(available=True, reason=None, metric="individual_measured_1rm",
            unit="kg", statistic="individual_observations",
            chart_kind="paired_points_no_interpolation",
            population={"description":"PER군 5명 등록·3명 분석, 비무작위 파일럿",
                "enrolled":5,"analyzed":3,"injury_withdrawals":2,
                "training_related_injury_withdrawals":1,"comparator_displayed":False},
            timepoint={"training_weeks":10,"pre":"baseline_test","post":"national_competition"})
        for exercise, pre, post in (
            ("barbell_back_squat",(200,175,175),(205,175,180)),
            ("barbell_bench_press",(145,120,140),(147.5,120,140)),
            ("barbell_deadlift",(230,165,200),(235,165,230))):
            for index,(before,after) in enumerate(zip(pre,post),1):
                for moment,value in (("pre",before),("post",after)):
                    result["points"].append(dict(panel_id=exercise,exercise_id=exercise,
                        participant_id=str(index),arm="PER_SOURCE_LABELS",
                        timepoint=moment,value=value,unit="kg",
                        selected=arm=="PER_SOURCE_LABELS"))
        result["limits"] += [
            "3명의 관측값을 모두 표시하며 평균 효과나 모집단의 효과로 확장하지 않아요.",
            "사후 측정은 전국대회 기록이므로 체육관 측정과 조건이 달라요.",
            "참가자 1의 총합 사후값·변화량·종목 합계에 불일치가 있어 총합 차트는 제외해요.",
            "보충자료의 프런트 스쿼트 표기와 본문의 SBD 설명은 불일치해요. 프런트 스쿼트 효과는 측정되지 않았어요.",
            "여기서는 PER군만 표시하며 MAX군에 대한 우월성 비교를 하지 않아요."]
        return result
    if identity in ("petrizzo2018-four-lift-2d-v1","petrizzo2018-four-lift-3d-v1"):
        result["source"].update(
            url="https://www.asep.org/asep/asep/JEPonlineOCTOBER2018_Petrizzo.pdf",
            locator="p.88 / Results / Protocol Completion", source_sha256=PETRIZZO_SHA,
            attribution="Petrizzo et al. (2018), JEPonline 21(5):84–96",
            license="not_asserted_link_and_numeric_facts_only")
        if arm not in (None, "FOUR_LIFT"):
            return _unavailable(result, "arm_not_reviewed", "이 선택안과 연결한 결과가 없어요.")
        expected = {"recruited":58,"analyzed":40,"completed_12_weeks":24,
                    "stalled":15,"injury_withdrawal":1,"other_excluded_dropouts":18}
        if any(source.get("study",{}).get(k)!=v for k,v in expected.items()):
            return _unavailable(result,"source_revision_unreviewed","원문과 대조한 참여자 수가 달라 표시하지 않아요.")
        result.update(available=True,reason=None,metric="participant_flow",
            unit="participants",statistic="observed_counts",chart_kind="categorical_counts",
            population={"description":"저항훈련 경험이 없는 남녀 58명 모집·40명 분석",
                "recruited":58,"analyzed":40,"design":"supervised_single_cohort_no_randomized_comparator"},
            timepoint={"maximum_training_weeks":12})
        for category,label,n in (
            ("completed_12_weeks","12주 완료",24),
            ("progression_stalled","증량 지속 불가",15),
            ("injury_withdrawal","부상으로 중단",1),
            ("other_excluded_dropouts","시간 부족·비훈련 관련 질환으로 분석 제외",18)):
            result["points"].append(dict(category=category,label=label,value=n,
                unit="participants",denominator=58))
        result["limits"] += [
            "근력 향상량이 아니라 연구 참여자의 진행 결과예요.",
            "24명 완료는 분석자 40명 중 60%예요. 모집자 58명 전체의 60%가 아니에요.",
            "주 2회와 3회는 별도 무작위 실험군이 아니므로 같은 연구 결과를 공유해요.",
            "실시간 감독하의 결과를 앱 단독 사용의 안전성이나 개인 완료 확률로 해석하지 않아요."]
        return result
    if identity in ("mugemuge-sbd-foundation-v1","mugemuge-sbd-trained-v1"):
        result["source"].update(url=source.get("evidence",{}).get("url"),
            locator=source.get("evidence",{}).get("locator"))
        return _unavailable(result,"product_synthesis_not_directly_tested",
            "이 8주 SBD 구성 자체를 실험한 결과가 없어요. 일반 저항훈련 근거를 이 루틴의 효과 수치로 바꾸지 않아요.")
    if source.get("kind")=="self_guided_education_not_training":
        return _unavailable(result,"education_not_efficacy_trial",
            "입문 학습 경로는 효과 검증 실험이 아니므로 근력 향상 차트를 제공하지 않아요.")
    return _unavailable(result,"source_not_reviewed","검토된 결과 수치가 연결되지 않은 자료예요.")

