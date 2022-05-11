odoo.define('website_menu_url_translate.contentMenu', function (require) {
'use strict';

var contentMenu = require('website.contentMenu');
var MenuEntryDialog = contentMenu.MenuEntryDialog;

contentMenu.EditMenuDialog.include({
	edit_menu: function (ev) {
		var self = this;
        var menu_id = $(ev.currentTarget).closest('[data-menu-id]').data('menu-id');
        var menu = self.flat[menu_id];
        this.elem = '';
        if (menu) {
            var dialog = new MenuEntryDialog(this, {}, undefined, menu);
            dialog.on('save', this, function (link) {
                var id = link.id;
                var menu_obj = self.flat[id];
                _.extend(menu_obj, {
                    'name': link.text,
                    'url': link.url,
                    'new_window': link.isNewWindow,
                });
                var $menu = self.$('[data-menu-id="' + id + '"]');
                $menu.find('.js_menu_label').first().text(menu_obj.name);
            });
            dialog.open();
            $('.modal-dialog').find('li.clearfix').after(
              '<input type="checkbox" class="default_url"/>'+
              'Use the page or URL of the default language.');
        } else {
            Dialog.alert(null, "Could not find menu entry");
        }
        $('.default_url').click(function(e) {
			if($(this). prop("checked") == true){
				self.elem = $('#s2id_link-page a').children().clone();
				self._rpc({
		            route: '/defaulturl',
		            params: {
		            	menu_id: menu_id,
		            },
		        }).then(function (data) {
		        	if (data){
		        		$('#link-external').val('');
						$('#link-external').val(data);
						$('#link-external').prop("readonly", true);
						$('#s2id_link-page a').empty();
						$('#s2id_link-page').attr('disabled',true);
						$('#s2id_link-page').removeClass('select2-container');
		        	}

		        });
			} else {
				$('#link-external').prop("readonly", false);
				$('#s2id_link-page').removeAttr('disabled');
				$('#s2id_link-page').addClass('select2-container');
				self.elem.appendTo($('#s2id_link-page a'));
			}
		});
    },
});

});