"""앱 내장 조건: 엔진을 임포트해도 호스트의 로깅 설정과 작업 폴더를 건드리지 않는다.

AI 서버의 `app.ai.gates` 는 `app.utils.logger` 를 거쳐 루트 로거에 파일 핸들러를 붙이고
작업 폴더에 `storage/logs/` 를 만든다. 엔진으로 옮길 때 표준 `logging.getLogger` 로 바꿨다.
"""
import subprocess
import sys

_CHECK = (
    "import logging, os\n"
    "import semojum_braille.encoder.translator, semojum_braille.encoder.gates, semojum_braille.decoder\n"
    "assert logging.getLogger().handlers == [], logging.getLogger().handlers\n"
    "assert not os.path.exists('storage'), os.listdir('.')\n"
)


def test_임포트가_루트_로거와_작업폴더를_안_건드린다(tmp_path):
    subprocess.run([sys.executable, "-c", _CHECK], cwd=tmp_path, check=True)
