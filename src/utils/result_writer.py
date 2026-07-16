from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


RESULT_CSV_HEADERS = ["기록시간", "에이전트 제목", "삭제 결과", "비고"]


class DeleteResultWriter:
    """삭제 테스트 결과를 CSV로 저장합니다."""

    def __init__(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = output_dir / f"deleteagent_result_{timestamp}.csv"
        self.path.write_text("\ufeff", encoding="utf-8")
        print(f"삭제 결과 CSV 생성 완료: {self.path}")

    def write(self, agent_title: str, result: str, comment: str = "") -> None:
        file_size = self.path.stat().st_size if self.path.exists() else 0
        needs_header = file_size <= 3

        with self.path.open("a", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            if needs_header:
                writer.writerow(RESULT_CSV_HEADERS)
            writer.writerow(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    agent_title,
                    result,
                    comment,
                ]
            )

    def write_no_agent(self, delete_mode: str) -> None:
        if delete_mode == "automation":
            message = "삭제할 자동 생성 테스트용 에이전트가 없습니다."
        else:
            message = "삭제할 에이전트가 없습니다."
        self.write(message, "PASS", "삭제 대상 없음")
