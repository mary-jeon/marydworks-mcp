# SolidWorks COM/pywin32 자동화 실측 노트 (2026-09, SW 2024 SP5)

실제 프로젝트에서 검증된 것만 적음. 경로는 `<PROJECT_DIR>`·`<CAD_DIR>`로 익명화.

## solidworks-com-automation-facts

- MCP `sw_*`는 처음 붙은 SW 인스턴스에 고정. `sw_background`는 SW가 떠 있으면 `USER_SESSION_RUNNING` 거부. 새 창 작업은 pywin32로 ROT 모니커 `SolidWorks_PID_<pid>`를 골라 붙는다(사용자의 큰 창 PID엔 절대 안 붙음).
- late-binding: `GetDocuments`/`GetChildren`/`GetPackAndGo`는 호출(), `GetTitle`/`GetPathName`/`GetMathUtility`/`EditRebuild3`는 속성. byref 정수는 `VARIANT(VT_BYREF|VT_I4,0)`. `LoadFile4` ImportData=`app.GetImportFileData(path)`. `CreateTransform`은 막힘 → `Transform2.ArrayData` 교체.
- 변환은 행벡터 규약 p′=p·R+t. STEP 임포트 서브어셈블리의 로컬 원점은 유로 중심이었음(추정 말고 자식 박스로 확인).
- 파트문서 박스와 어셈블리 컴포넌트 박스는 부품별 수~16 mm 어긋남 → 삽입 후 실제 박스로 반복 보정.
- STEP 임포트 느리고(1 MB≈수십 초) 반복 시 SW 크래시 경험 → STEP은 한 번만 읽어 SLDPRT로 저장. **멀티파트 STEP을 어셈블리로 임포트해 저장하면 자식 파트가 SW 기본 폴더(=설계 폴더 Z:)에 생성됨** — 먼저 기본 폴더를 확인하거나 파트로 저장.
- 어셈블리→파트 저장 기본옵션은 "외부 면"(서피스 바디). 솔리드 필요하면 옵션 확인.
- Bash 툴 기본 2분 제한 → COM 장작업은 timeout 600000. 자동모드 분류기가 `ReplaceReferencedDocument`를 차단함.

**Why:** 2026-09-02 세션에서 이 항목마다 한 번씩 실패한 뒤 확인된 것.
**How to apply:** SolidWorks 자동화 시작 전에 이 목록대로 세팅하면 재시행 비용을 피한다. [[brine-injection-line-assembly]]
- (2026-09-08 실측) 컴포넌트 `Transform2` 설정은 **활성 구성에만** 들어가는 경우가 있다(같은 어셈블리에서 어떤 때는 공유, 어떤 때는 구성별). 이동 후 반드시 모든 구성을 돌며 다시 설정하고 구성별 box로 확인할 것. MCP `sw_audit`·`sw_snapshot`은 doc.configuration을 무시하고 활성 구성으로 돈다 → COM `ShowConfiguration2`로 바꾼 뒤 호출.
- (2026-09-08 실측) **판금 변환** `IFeatureManager.InsertConvertToSheetMetal2(t,False,FindBends,r,gap,0,0.5,0,0.5,False)`는 성공해도 **None**을 돌려준다 → 트리의 `SolidToSheetMetal` 피처와 체적(날카로운 모서리→굽힘 치환 계산값)으로 판정. 선택: 고정면 mark 1 + **고정면의 바깥 모서리**(이웃 벽과 만나는 변) mark 2 + FindBends=True 만 성공. 안쪽 모서리·립 mark 4·FindBends=False는 무반응, 모서리 없이 FindBends만 주면 벽이 잘려 나감. 4벽 뚜껑은 굽힘 4변만 주면 모서리 립 자동. `IPartDoc.InsertBends2`는 True 반환 후 피처 없음. 면 방향은 `PlaneParams`(뒤집힐 수 있음) 말고 `IFace2.Normal`. `InterferenceDetectionManager`는 `IAssemblyDoc` 속성(Extension 아님). `IFace2.GetEdges`·`IEdge.GetTwoAdjacentFaces2`·`IBody2.GetFaces`는 속성(pv). 스크립트 `_scripts/sheetmetal_convert_0908.py`.
- (2026-09-08) 어셈블리에서 컴포넌트를 지워도 그 파트 문서는 `CloseDoc`로 안 닫히고(`~$` 잠금 유지) 파일 이동 불가 → SW 종료 후 이동. 백업 복사(copy)는 잠긴 상태에서도 된다.

**2026-09-09 실측 추가**
- `IComponent2.Transform2` 설정은 **구성별이 아니라 전 구성에 적용**된다(구성별 위치가 필요하면 인스턴스를 나눠 구성별 억제). 잠금(Lock) 메이트가 걸린 컴포넌트를 Transform2로 옮기면 메이트 재해석 시 엉뚱한 오프셋으로 튄다 → 메이트 삭제 후 FixComponent.
- `IFeatureManager.InsertMoveCopyBody2` 실제 인수 순서(makepy): (TransX, TransY, TransZ, TransDist, RotPointX, RotPointY, RotPointZ, RotAngleX, RotAngleY, RotAngleZ, Copy, N). **실측: 10번째 슬롯 각도가 X축 회전, 8번째가 Z축 회전**(문서 이름과 반대). 회전 중심은 5~7번째.
- 부분 간섭 검사: 컴포넌트 `Select4(True,NOD,False)`로 선택 후 `InterferenceDetectionManager.GetInterferences`(선택 기반, AddComponents 메서드 없음). 서브어셈블리 Name2는 상위 경로를 포함하므로 `split("/")[-1]`.
- 컴포넌트 참조구성(`ReferencedConfiguration`)·억제·고정 상태는 구성별로 저장된다.

- 2026-09-09: SolidWorks 인스턴스가 2개(다른 프로젝트 PID 22020 + 스테이션 18704) 뜨면 ROT 첫 항목이 엉뚱한 쪽일 수 있다. `swconn.connect()`는 이제 `SW_PID` 환경변수 → 「염수주입라인/S00000MU0가 열린 인스턴스」 순으로 고른다. 스크립트가 아무것도 못 찾고 조용히 지나가면 먼저 이걸 의심.
- 컷 대상 스케치의 사각형에 치수가 없으면(J1c 스케치3) 선분을 지우고 같은 스케치 안에 다시 그리면 피처가 유지된다(스케치 삭제 아님).

- **간섭검사 플래그(09-09 실측)**: 파트만 있는 어셈블리(염수주입라인)에서 `InterferenceDetectionManager.TreatSubAssembliesAsComponents=True`를 주면 `GetInterferences`가 **빈 결과(거짓 0)**를 돌려준다. 서브어셈블리가 있는 S00000MU0에서는 True/False 모두 정상. 규칙: 파트 전용 어셈블리에서는 그 플래그를 건드리지 말고, 검사마다 **양성 대조(알려진 나사 겹침 G14↔밸브 등)가 나오는지**로 검사 자체를 검증한다.
- **FeatureCut4 ThroughAll(T1=1)·ThroughAllBoth(T1=9)는 한쪽만 자른다**(실측: 탭 18 두께 중 9만 컷). 양방향 관통이 필요하면 바깥쪽 오프셋 기준면(InsertRefPlane 8|256)에 스케치하고 블라인드로 전체 두께를 지나가게 컷한다(방향은 결과 원통면으로 판정 후 반대면 재시도).
- **FeatureExtrusion3의 T0=1 StartOffset**은 이 환경에서 None을 돌려주거나 반대쪽으로 갔다 → 오프셋 기준면 + 일반 돌출로 대체. `InsertRefPlane(8|256, d)`는 −쪽, `8`만 주면 +쪽.
- **Simulation 알림 모달**(#32770 'Simulation', 버튼 1개 '확인' — 「메시 정보가 최신이 아닙니다」)이 어셈블리 구성 전환마다 떠서 COM을 막는다 → `swconn.watchdog()`가 단일 버튼 Simulation 대화상자를 자동 클릭하도록 확장(09-09). 스터디가 있는 어셈블리에서 부품을 지우면 스터디는 무효.

- **(2026-09-10 실측) 제조사 STEP(어셈블리 구조) → 단일 파트 합성**: `LoadFile4`로 STEP 어셈블리를 열면 「SOLIDWORKS 새 문서」 템플릿 대화상자가 COM을 막는다 → `_scripts/swdialog.py`의 `template_clicker()`(스레드, '확인' SendMessage)로 통과. 자식 파트는 `C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\spiop\`에 메모리 문서로 생김(저장 안 하면 파일 없음). **「어셈블리를 파트로 저장」(`SaveAs3` + `IAdvancedSaveAsOptions.GeometryToSave=1`, `OverrideDefaults=True`, 시스템 옵션 `swSaveAssemblyAsPartOptions(201)=1`까지 줘도) 결과는 곡면(sheet) 바디만 남는다(3회 재현)** → 대신 자식 파트를 SaveAs 후 새 파트에 `InsertPart3(file, 1|512|262144, "")`로 넣고 `InsertMoveCopyBody2`로 원 변환을 재적용(`ke002_build_b4c_0910.py`).
- `InsertMoveCopyBody2`: 바디 선택은 `CreateSelectData` **Mark=1** 필수(없으면 None). 회전 인수는 문서 표기와 달리 **8번째=Z축, 9번째=Y축, 10번째=X축**(우수 양의 각, 라디안). 합성 회전은 외재적 xyz 오일러각을 축별 **별도 피처 3개**로 나눠 적용하고 무게중심(`GetMassProperties[0:3]`)으로 검증. 바디 이름은 이동 피처마다 바뀌므로 바디 추적은 이름이 아니라 박스로.
- `GetBodies2(type)`: 0=솔리드, **1=곡면(sheet)**, −1=전부. `IComponent2.GetBox`는 회전된 바디에서 느슨한 박스를 준다(무게중심으로 검증할 것). `ReplaceComponents2(File, Cfg, ReplaceAll, UseConfigChoice, ReAttachMates)` 5인수. 고정 컴포넌트 `Transform2`는 전 구성 공통(§1-26 재확인).
- 파트만 있는 어셈블리 간섭검사에서 `TreatSubAssembliesAsComponents=True`는 **거짓 0** → False + 양성 대조(나사 겹침) 확인. `IncludeMultibodyPartInterferences=True`면 다중바디 파트(B4c) 내부 겹침(나사↔탭)이 같은 컴포넌트 쌍으로 나온다.

## stair-round-0922

2026-09-22 저장 기준. 상세 HANDOFF.md §0-12. 스크립트 `_scripts\stair_round_0922.py`·`stair_round2_0922.py`·`stair_round3_0922.py`, 백업 `sw-mcp\_backup\20260922-stair-round\`.

- **사용자 강한 지시**: 「stair handrail은 돌려내라, 내가 직접 모델링한 건데」 → 사용자가 만든 파트(S20017-1)는 대체하지 말고 **그 파트를 살려서 맞춘다**. 사용자 파일 수정은 형태·치수를 최소로(경사 치수 하나, 끊긴 컷 재작성, 끝 컷 추가)만 하고 REMARK에 무엇을 바꿨는지 적는다. 「오른쪽 가로대 없음」은 확인된 배치.
- 지면 = **로봇 타이어 접지 x 1,100.2**(골조 하단 1,050보다 50.2 아래; 골조가 떠 있는 것은 사용자 편집 영역).
- 결과: S20000 오류 0·간섭 0. 계단 8단 227.49×205(47.98°), 손잡이 다리 하단 = 측판 윗면선(155.0), 위쪽 끝 = 앞 원형 지주 앞면 996.15.
- **판금 변환 API(실측)**: `InsertConvertToSheetMetal2` — 닫힌 ㅁ(슬릿 1)은 고정면 mark1 + 바깥 모서리 4개 mark2 + FindBends=False만 성공; 바깥 모서리는 회전축 좌표(x 0/±50)로 선택; 실패 후 피처 삭제 시 모서리 객체 끊김 → 재선택; 변환 후 플랜지 끝 3.05 초과 재생성 → 끝 컷 재적용. ㄷ은 상면+긴 변 2+FindBends=True. δ=(1−π/4)(2rt+t²).
- **사용자 파트 분석 요령**: 백업을 다른 이름으로 복사해 읽기 전용으로 열고, 피처 억제 전후 체적·무게중심·평면 면 목록 diff로 컷의 역할을 읽는다(면 스케치의 ModelToSketchTransform t 는 해석 불가). 관계로 묶인 치수 없는 선은 SetCoords 무시됨. 회전 배치 컴포넌트는 Transform2 ArrayData에 R 넣고 기준면 메이트 정렬 변형을 돌려 R·t 일치로 판정.
- 미참조: 내 S20020(삭제 후보, 승인 대기). 남은 것: 기둥 캡, 용접 표현, SR-ST-05 갱신. [[stair-redesign-0917]] [[brine-line-down22-0922]] [[solidworks-com-automation-facts]]

## brine-line-down22-0922

2026-09-22 저장 기준. 상세 HANDOFF.md §0-11. 현재 라인 = 09-21 상태(J1d·J5p·J25a 슬리브, §0-10) + 이 변경.

- 지시 흐름: 「하강 시 호스 22.21 더」→「이동판 전체」→ A안(고정 러그 J8h 연장) 완료 → 사용자 「브래킷 말고 실린더 긴 걸, 하강 540~550, **스트로크 150 고정**」(이유: 노즐이 로봇 해치 안에 들어가야 튀지 않음) → A안 원복, **TA2 RL 314**로 재작업.
- 최종: 거리_상승/하강 **400/550**, TA2 **B9l** TA2-2H-150314-5511-010-1(TraceParts STEP, 후단 핀 원점 규약 동일, 마운트 z 26·J8g·G11f 불변), 봉 **J2f PSSFAQ20-630**(끝 −643, 여유 21), 호스 **J19p**(자유길이 592, 절단 697, 고리 190/142). 스테이션 라인↔외부 간섭 0. 노즐 끝 지상고 하강 1,464(로봇 상판 bbox 안 9.8 = 해치 개구 안, 실형상 0).
- TA2 RL은 데이터시트 p.6 하한(≥Stroke+Y)만 있고 상한 없음 → 주문 시 RL 지정 가능. 발주 표기 RL 274→314 개정 필요.
- TraceParts 다운로드 실측: goto URL → 사용자 로그인(ELS 영역에서 다시 풀림, SIGN IN 재클릭) → 사이트 CAPTCHA + 다운로드 captcha는 사용자가 입력 → 1차 「delivery failed」, 2차 성공. 구성기는 필드 바꿀 때마다 re-render → form_input ref 무효, **JS로 label→select/input 찾아 value+change 이벤트, Load code를 바꾸면 Stroke·RL이 초기화되므로 Stroke·RL은 마지막에**. PartNumber는 URL에 반영.
- 미참조 삭제 후보(승인 대기, 7): J8h·J2e-605·J19o×2(A안)·J2d-580·J19n×2 (+B9k RL 274).
- 실측: 윗면(Top) 스케치 ModelToSketchTransform은 전치 규약(conv 1); `CreateCornerRectangle` 반환은 raw IDispatch 튜플 → `_wrap`. 사용자 단일 SW 인스턴스(PID 14016)에서 S00000 구성 전환 검사 후 복귀는 문제 없었음. 같은 인스턴스에 COM 스크립트 2개 동시 실행은 피함(순차). [[brine-line-stroke150-0917]] [[solidworks-com-automation-facts]]

## brine-line-stroke150-0917

2026-09-17 저장 기준. 상세 HANDOFF.md §0-03·§0-02·§2-6. 정본 `Z:\…\S_BrineCharge Station\염수주입라인.SLDASM`, 백업 `sw-mcp\_backup\20260917-stroke150\`(09-15 상태).

- **결정**: 스트로크 150은 **B안** — 상승 ZP −360(노즐 1,604) / 하강 −510(1,454). A안(하강 65 더)은 로봇 상면(1,466~1,491)과 이동판 겹침으로 불가. TA2 = TA2-2H-150, **Retracted Length 274**(≥150+119) → 발주 표기 변경. 3D는 TraceParts 150274 STEP **B9k**로 교체 완료(09-17 저녁).
- **가이드 4점**: 앞 x 0 / 뒤 x 90, y ±240. LHFRW20(D32 L80 PCD43 M5, 재질 원문 「[철] SUJ2 상당」)·PSSFAQ20-580-B13(하단 지상고 1,460)·SHFSS20(M6, L 방향 y). J1c Ø20.5×4+M6×8. 3D 전부 규격표 치수 모델 → STEP 교체 대기(TraceParts·MISUMI 로그인이 **엣지**에 있어 크롬 확장 자동화로는 미로그인 — 크롬 로그인 또는 엣지 수동 다운로드 필요).
- **호스(09-17 오후)**: 사용자 정정 「120 = 접힌 고리 바깥 폭」→ 상승 시 190. 세로 간격 81뿐이라 **나선 1회전 고리**로 흡수, 나가는 다리 (0,+45)(소켓·노즐·호스니플 y +45), 고리는 −x(앞, KE005 밑, 상단 직선 50). 절단 ≈657. 1차안(x −45)은 하강 노즐↔열린 뚜껑 4.4 겹침으로 폐기. 이동판 J5n(180×540, 구멍 (0,45)). 스테이션 간섭 0. 잔여 = 호스↔클램프/니플 접촉 수치오차(≤32 mm³).
- **계단 3건은 09-17 저녁 완료** → [[stair-redesign-0917]]. MISUMI 3종 STEP은 크롬 MISUMI 탭 로그인 후 진행(부시 재질 원문 「[철] SUJ2 상당」 → B10b Material 갱신도 그때).
- **미참조 삭제 승인 대기(7)**: J5l·J5m·J19k×2·J19m×2·B9j (`_검증\unused_candidates_0917c.txt`). 09-17 승인분 11개는 삭제 완료.
- **자동화 실측**: 스플라인 스윕 GetBodyBox 과대(체적으로 검증), 면 스케치는 ModelToSketchTransform으로 프로파일을 경로 시작점에, 직선은 돌출·곡선만 스윕, 컴포넌트 SetSuppression2 단일 인수, FeatureCut4 Sd=False 양방향, 참조 중 파트는 ReloadOrReplace로 폐기. [[solidworks-com-automation-facts]] [[brine-line-50a-telescopic]]
