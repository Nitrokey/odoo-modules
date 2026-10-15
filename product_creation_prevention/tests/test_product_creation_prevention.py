from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

# groups that the module's ir.model.access.csv restricts to read-only
GROUPS = [
    "base.group_user",
    "sales_team.group_sale_manager",
    "account.group_account_manager",
    "stock.group_stock_manager",
    "mrp.group_mrp_manager",
    "purchase.group_purchase_manager",
    "product.group_product_manager",
]


@tagged("post_install", "-at_install")
class TestProductCreationPrevention(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env["product.template"].create({"name": "Protected"})
        cls.product = cls.template.product_variant_id
        cls.users = {}
        for group in GROUPS:
            login = "ppc_" + group.split(".")[1]
            cls.users[group] = cls.env["res.users"].create(
                {
                    "name": login,
                    "login": login,
                    "email": f"{login}@example.com",
                    "groups_id": [(6, 0, cls.env.ref(group).ids)],
                }
            )

    def _check(self, user, model, operation):
        self.env[model].with_user(user).check_access(operation)

    def test_read_allowed(self):
        for group, user in self.users.items():
            for model in ("product.template", "product.product"):
                with self.subTest(group=group, model=model):
                    self._check(user, model, "read")
        # reading actual records works too
        user = self.users["base.group_user"]
        self.assertEqual(self.template.with_user(user).name, "Protected")
        self.assertEqual(self.product.with_user(user).name, "Protected")

    def test_write_create_unlink_denied(self):
        for group, user in self.users.items():
            for model in ("product.template", "product.product"):
                for operation in ("write", "create", "unlink"):
                    with self.subTest(group=group, model=model, op=operation):
                        with self.assertRaises(AccessError):
                            self._check(user, model, operation)

    def test_create_record_denied(self):
        user = self.users["product.group_product_manager"]
        with self.assertRaises(AccessError):
            self.env["product.template"].with_user(user).create({"name": "Nope"})
        with self.assertRaises(AccessError):
            self.env["product.product"].with_user(user).create({"name": "Nope"})

    def test_write_record_denied(self):
        user = self.users["stock.group_stock_manager"]
        with self.assertRaises(AccessError):
            self.template.with_user(user).write({"name": "Changed"})

    def test_superuser_can_create(self):
        template = self.env["product.template"].sudo().create({"name": "Allowed"})
        self.assertTrue(template.exists())

    def test_access_rights_are_overridden(self):
        """The module's CSV overrides the access records of the other modules."""
        access = self.env.ref("product.access_product_template_manager")
        self.assertTrue(access.perm_read)
        self.assertFalse(access.perm_write)
        self.assertFalse(access.perm_create)
        self.assertFalse(access.perm_unlink)
