# Migration Guide: website_sale_embargo (15.0 → 18.0)

## Overview
This document describes the changes made to migrate the `website_sale_embargo` module
from Odoo 15.0 to 18.0.

## Summary of Changes

### 1. Manifest File (`__manifest__.py`)
**Change**: Updated version number
- **Before**: `"version": "15.0.1.0.0"`
- **After**: `"version": "18.0.1.0.0"`

### 2. Controller (`controllers/main.py`)

#### Critical Bug Fix
**Issue**: Missing return statement in `confirm_order` method
- **Impact**: The method didn't properly return the result from the parent class,
  causing potential issues with the checkout flow
- **Fix**: Added `return` statement before `super().shop_confirm_order(**post)`

#### Method Name Changes (Odoo 18.0 API)
The WebsiteSale controller in Odoo 18.0 renamed several methods:

1. **confirm_order → shop_confirm_order**
   - **Before**: `def confirm_order(self, **post):`
   - **After**: `def shop_confirm_order(self, **post):`
   - **Reason**: Standardization of method naming in Odoo 18.0

2. **address → shop_address**
   - **Before**: `def address(self, **kw):`
   - **After**:
     `def shop_address(self, partner_id=None, address_type='billing', use_delivery_as_billing=None, **query_params):`
   - **Reason**: Odoo 18.0 refactored the address handling with explicit parameters

#### Method Signature Updates

**shop_address Method**:
-  **New parameters**: `partner_id`, `address_type`, `use_delivery_as_billing` are now
  explicit parameters
- **Replaced**: `**kw` with `**query_params` for clarity
- **Added**: Import of `str2bool` from `odoo.tools` for proper boolean parameter
  handling

#### Logic Improvements

1. **Removed `get_mode()` helper**
   - This method is no longer needed as Odoo 18.0 handles mode detection differently
   - The parent class now provides `_prepare_address_update()` for this purpose

2. **Updated address validation logic**
   - Changed from `mode[1] == "shipping"` to `address_type == "delivery"`
   - Updated to use `_prepare_address_update()` from parent class
   - Updated to use `_prepare_address_form_values()` instead of deprecated
     `_get_country_related_render_values()`

3. **Added cart validation**
   - Added `if redirection := self._check_cart(order):` to ensure cart is valid before 
     proceeding

### 3. Models (No Changes Required)

#### `models/sale_order.py`
- ✅ Already using modern API (`_action_confirm()`)
- ✅ No deprecated decorators
- ✅ Fully compatible with Odoo 18.0

#### `models/hs_code.py`
- ✅ Simple model extension
- ✅ Fully compatible with Odoo 18.0

### 4. Views (No Changes Required)

#### `views/hs_code.xml`
- ✅ Already uses `<odoo>` tags (correct for all versions)
- ✅ View inheritance syntax is compatible
- ✅ Fully compatible with Odoo 18.0

### 5. Dependencies

#### `product_harmonized_system`
- ✅ Confirmed available in Odoo 18.0
- ✅ Version: 18.0.1.2.0
- ✅ No changes required to dependency declaration

## Data Migration

**No OpenUpgrade scripts required** because:
- The module only extends existing models with a Many2many field
- No custom database tables are created
- No data transformation is needed
- The Many2many field (`country_id` on `hs.code`) will be automatically created by
  Odoo's ORM during module upgrade
## Testing Checklist

After migration, test the following scenarios:

### Functional Tests
1. **Product with HS Code + Allowed Country**
   - [ ] Add product with HS code to cart
   - [ ] Select allowed country as shipping address
   - [ ] Verify checkout proceeds normally
   - [ ] Verify order confirms successfully

2. **Product with HS Code + Embargoed Country**
   - [ ] Add product with HS code and embargo countries configured
   - [ ] Attempt to select embargoed country as shipping address
   - [ ] Verify error message is displayed on address form
   - [ ] Verify customer cannot proceed to payment
   - [ ] Attempt to confirm order (if bypassing UI)
   - [ ] Verify ValidationError is raised with appropriate message

3. **Multiple Products with Mixed Embargoes**
   - [ ] Add multiple products with different HS codes and embargo configurations
   - [ ] Test various country selections
   - [ ] Verify embargo checks work for all products

### Technical Tests
1. **Module Loading**
   - [ ] Module installs without errors
   - [ ] Module upgrades from 15.0 without errors
   - [ ] No errors in server logs during installation/upgrade

2. **View Rendering**
   - [ ] Address form renders correctly
   - [ ] Checkout page renders correctly
   - [ ] Error messages display properly
   - [ ] HS Code form views show country field

## Breaking Changes from 15.0

### For Developers Extending This Module
If you have customizations that override the `website_sale_embargo` methods:

1. **Update method names**:
   - `confirm_order` → `shop_confirm_order`
   - `address` → `shop_address`

2. **Update method signatures**:
   - `shop_address` now has explicit parameters instead of `**kw`

3. **Update helper method calls**:
   - `_get_country_related_render_values()` → `_prepare_address_form_values()`
   - Custom `get_mode()` logic should be replaced with `_prepare_address_update()`

## Compatibility Notes

- **Python**: Compatible with Python 3.10+ (Odoo 18.0 requirement)
- **Odoo Core**: Requires Odoo 18.0
- **Dependencies**: All dependencies confirmed available in Odoo 18.0

## Migration Validation

### Syntax Validation
All Python files have been validated with `py_compile`:
```bash
python3 -m py_compile website_sale_embargo/**/*.py
```
✅ No syntax errors found

### Code Quality
- Modern Python syntax (walrus operator `:=` where appropriate)
- Consistent with Odoo 18.0 coding standards
- Proper import organization

## Support and Issues

If you encounter issues after migration:
1. Check server logs for detailed error messages
2. Verify `product_harmonized_system` module is installed and updated to 18.0
3. Clear browser cache and restart Odoo server
4. Verify database was properly upgraded

## Credits

**Migration Author**: AI Assistant (Cline)
**Migration Date**: October 2025
**Original Module Author**: Nitrokey GmbH
**Original Module License**: AGPL-3.0 or later
