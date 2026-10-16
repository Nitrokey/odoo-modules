# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import json

from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestIotQualityControl(HttpCase):
    readonly_enabled = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({"name": "Device"})
        cls.production = cls.env["mrp.production"].create(
            {"product_id": cls.product.id, "product_qty": 1}
        )
        cls.inspection = cls.env["qc.inspection"].create(
            {
                "name": "Test Inspection",
                "object_id": f"mrp.production,{cls.production.id}",
            }
        )
        cls.system = cls.env["iot.communication.system"].create({"name": "System"})
        cls.device = cls.env["iot.device"].create(
            {"name": "Device", "communication_system_id": cls.system.id}
        )
        cls.serial = "qcdeviceserial"
        cls.passphrase = "qcpassphrase"
        cls.env["iot.device.input"].create(
            {
                "name": "Multi input",
                "device_id": cls.device.id,
                "serial": cls.serial,
                "passphrase": cls.passphrase,
                "call_function": "parse_multi_input",
            }
        )
        model = cls.env.ref("iot_quality_control.model_iot_quality_control")
        cls.cpu_input = cls.env["iot.device.input"].create(
            {
                "name": "CPU",
                "device_id": cls.device.id,
                "address": "cpu",
                "call_model_id": model.id,
                "call_function": "post_measurement",
            }
        )

    def _create_inspection(self, **vals):
        return self.env["qc.inspection"].create(
            {
                "name": "Extra Inspection",
                "object_id": f"mrp.production,{self.production.id}",
                **vals,
            }
        )

    def _notes(self):
        return self.inspection.message_ids.filtered(
            lambda m: m.subtype_id == self.env.ref("mail.mt_note")
        )

    def _post(self, values):
        response = self.url_open(
            f"/iot/{self.serial}/multi_input",
            data={"passphrase": self.passphrase, "values": json.dumps(values)},
        )
        return response.json()

    def test_post_measurement(self):
        result = self.cpu_input.call_device(
            value="Intel N100", mo_id=self.production.id
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("cpu", self._notes()[:1].body)
        self.assertIn("Intel N100", self._notes()[:1].body)

    def test_post_measurement_escapes_html(self):
        self.cpu_input.call_device(value="<script>x</script>", mo_id=self.production.id)
        self.assertNotIn("<script>", self._notes()[:1].body)

    def test_invalid_mo(self):
        self.assertEqual(
            self.cpu_input.call_device(value="x", mo_id="abc")["status"], "error"
        )
        self.assertEqual(
            self.cpu_input.call_device(value="x", mo_id=0)["status"], "error"
        )
        self.assertEqual(
            self.cpu_input.call_device(value="x", mo_id=self.production.id + 1000)[
                "status"
            ],
            "error",
        )

    def test_no_inspection(self):
        other = self.env["mrp.production"].create(
            {"product_id": self.product.id, "product_qty": 1}
        )
        result = self.cpu_input.call_device(value="x", mo_id=other.id)
        self.assertEqual(result["status"], "error")

    def test_test_parameter_filters(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "iot_quality_control.qc_test_id", "999999"
        )
        result = self.cpu_input.call_device(value="x", mo_id=self.production.id)
        self.assertEqual(result["status"], "error")

    def test_missing_key(self):
        result = self.env["iot.quality.control"].post_measurement(
            value="x", mo_id=self.production.id
        )
        self.assertEqual(result["status"], "error")
        self.assertFalse(self._notes())

    def test_mo_id_none(self):
        self.assertEqual(
            self.cpu_input.call_device(value="x", mo_id=None)["status"], "error"
        )

    def test_note_only(self):
        state = self.inspection.state
        lines = self.inspection.inspection_lines
        self.cpu_input.call_device(value="x", mo_id=self.production.id)
        self.assertEqual(self.inspection.state, state)
        self.assertEqual(self.inspection.inspection_lines, lines)

    def test_get_inspection_prefers_open(self):
        closed = self._create_inspection()
        closed.state = "canceled"
        model = self.env["iot.quality.control"]
        self.assertEqual(model._get_inspection(self.production), self.inspection)
        # the most recent one wins among open inspections
        newer = self._create_inspection()
        self.assertEqual(model._get_inspection(self.production), newer)
        # fall back to closed inspections when none is open
        (self.inspection | newer).state = "canceled"
        self.assertEqual(model._get_inspection(self.production), newer)

    def test_get_inspection_test_parameter(self):
        test = self.env["qc.test"].create({"name": "Test"})
        other = self._create_inspection(test=test.id)
        model = self.env["iot.quality.control"]
        param = self.env["ir.config_parameter"].sudo()
        param.set_param("iot_quality_control.qc_test_id", str(test.id))
        self.assertEqual(model._get_inspection(self.production), other)
        # a non-numeric value is ignored
        param.set_param("iot_quality_control.qc_test_id", "abc")
        self.assertTrue(model._get_inspection(self.production))

    def test_template(self):
        template = self.env.ref("iot_quality_control.iot_template_quality_control")
        device = self.env["iot.device"].create(
            {"name": "From template", "communication_system_id": self.system.id}
        )
        template.apply_template(device, template._get_keys("templateserial"))
        multi = device.input_ids.filtered(
            lambda i: i.call_function == "parse_multi_input"
        )
        self.assertEqual(len(multi), 1)
        self.assertEqual(
            set(device.input_ids.mapped("address")) - {False}, {"cpu", "ram", "storage"}
        )
        response = self.url_open(
            f"/iot/{multi.serial}/multi_input",
            data={
                "passphrase": multi.passphrase,
                "values": json.dumps(
                    [
                        {
                            "address": key,
                            "value": key.upper(),
                            "mo_id": self.production.id,
                        }
                        for key in ("cpu", "ram", "storage")
                    ]
                ),
            },
        )
        self.assertEqual([r["status"] for r in response.json()], ["ok"] * 3)
        self.assertEqual(len(self._notes()), 3)

    def test_multi_input_endpoint(self):
        result = self._post(
            [
                {"address": "cpu", "value": "i7", "mo_id": self.production.id},
                {"address": "unknown", "value": "x", "mo_id": self.production.id},
            ]
        )
        self.assertEqual(result[0]["status"], "ok")
        self.assertEqual(result[1]["status"], "error")
        self.assertEqual(len(self._notes()), 1)
