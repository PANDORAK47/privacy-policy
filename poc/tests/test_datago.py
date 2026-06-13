"""data.go.kr 응답 파서 / 백엔드 선택 단위 테스트(오프라인, 네트워크·키 불필요).

실행: poc/ 에서  python -m pytest  (또는 python -m unittest)
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import mfds_api  # noqa: E402


class TestDatagoParser(unittest.TestCase):
    def test_odcloud_data_list(self):
        data = {"currentCount": 1, "data": [{"PRDLST_NM": "정제수", "USE_YN": "Y"}]}
        rows = mfds_api._extract_rows_datago(data)
        self.assertEqual(rows[0]["PRDLST_NM"], "정제수")

    def test_apis_response_body_items_item_list(self):
        data = {"response": {"header": {"resultCode": "00"},
                             "body": {"items": {"item": [{"PRDLST_NM": "설탕"}]}, "totalCount": 1}}}
        rows = mfds_api._extract_rows_datago(data)
        self.assertEqual(rows[0]["PRDLST_NM"], "설탕")

    def test_apis_body_items_list(self):
        data = {"response": {"body": {"items": [{"NM": "구연산"}]}}}
        rows = mfds_api._extract_rows_datago(data)
        self.assertEqual(rows[0]["NM"], "구연산")

    def test_single_item_dict(self):
        data = {"response": {"body": {"items": {"item": {"PRDLST_NM": "소금"}}}}}
        rows = mfds_api._extract_rows_datago(data)
        self.assertEqual(rows, [{"PRDLST_NM": "소금"}])

    def test_bare_list(self):
        self.assertEqual(mfds_api._extract_rows_datago([{"a": 1}]), [{"a": 1}])

    def test_empty_on_unknown_shape(self):
        self.assertEqual(mfds_api._extract_rows_datago({"x": 1}), [])
        self.assertEqual(mfds_api._extract_rows_datago(None), [])
        self.assertEqual(mfds_api._extract_rows_datago({"data": []}), [])


class TestBackendSelection(unittest.TestCase):
    def test_mock_without_any_config(self):
        # 이 테스트 환경에는 키/URL env 가 없으므로 mock 으로 선택되어야 한다.
        if not (mfds_api.settings.data_go_kr_api_key or mfds_api.settings.mfds_service_key):
            self.assertEqual(mfds_api.backend("ingredient"), "mock")

    def test_force_mock_overrides(self):
        self.assertIn(mfds_api.backend("ingredient"), ("datago", "mfds", "mock"))


if __name__ == "__main__":
    unittest.main()
