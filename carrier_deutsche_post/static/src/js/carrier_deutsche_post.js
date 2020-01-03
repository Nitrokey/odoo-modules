odoo.define('nitrokey_carrier_deutsche_post.actionmanager', function (require) {
"use strict";

var ActionManager= require('web.ActionManager');
var session = require('web.session');
var pyeval = require('web.pyeval');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');

ActionManager.include({
	_executeURLAction: function (action, options) {
        var url = action.url;
        if (config.debug && url && url.length && url[0] === '/') {
            url = $.param.querystring(url, {debug: config.debug});
        }
        
        if (action.target === 'download') {
        	framework.redirect(url);
        }
        else if (action.target === 'self') {
            framework.redirect(url);
            return $.Deferred();
        } else {
            var w = window.open(url, '_blank');
            if (!w || w.closed || typeof w.closed === 'undefined') {
                var message = _t('A popup window has been blocked. You ' +
                             'may need to change your browser settings to allow ' +
                             'popup windows for this page.');
                this.do_warn(_t('Warning'), message, true);
            }
        }

        options.on_close();

        return $.when();
    },
	/*ir_actions_download: function (action, options) {
        var self = this;
        //instance.web.blockUI();
        framework.blockUI();
        action = _.clone(action);
        
        var user_context = this.getSession().user_context;
        var eval_contexts = ([user_context] || []).concat([action.context]);
        action.context = pyeval.eval('context', eval_contexts);
        
        var c = instance.webclient.crashmanager;
        return $.Deferred(function (d) {
        	session.get_file({
                url: action.url,
                data: {data: JSON.stringify(action.data)},
                complete: framework.unblockUI,
                error: crash_manager.rpc_error.bind(crash_manager),
            });
        });
    },*/
});

});

/*openerp.nitrokey_carrier_deutsche_post = function(instance) {

    instance.web.ActionManager = instance.web.ActionManager.extend({
        ir_actions_download: function (action, options) {
            var self = this;
            instance.web.blockUI();
            action = _.clone(action);
            var eval_contexts = ([instance.session.user_context] || []).concat([action.context]);
            action.context = instance.web.pyeval.eval('contexts',eval_contexts);
            var c = instance.webclient.crashmanager;
            return $.Deferred(function (d) {
                self.session.get_file({
                    url: action.url,
                    data: {data: JSON.stringify(action.data)},
                    complete: instance.web.unblockUI,
                    success: function(){
                        if (!self.dialog) {
                            options.on_close();
                        }
                        self.dialog_stop();
                        d.resolve();
                    },
                    error: function () {
                        c.rpc_error.apply(c, arguments);
                        d.reject();
                    }
                });
            });
        },
    });

    instance.nitrokey_carrier_deutsche_post.PickingEditorWidgetExtended = instance.stock.PickingEditorWidget.include({
        download_label: function(){
            var self = this;
            var parent = self.getParent();
            return new instance.web.Model('stock.picking').call('get_deutsche_post_label',[[parent.picking.id]])
                .then(function(action){
                    self.$('.js_de_label_buy').fadeOut()
                    self.$('.js_de_label_download').fadeIn()
                    return self.do_action(action);
            });
        },
        renderElement: function(){
            var self = this;
            this._super();
            picking = self.getParent().picking
            this.$('.js_de_label_buy').click(function(){ self.download_label(); });
            this.$('.js_de_label_download').click(function(){ self.download_label(); });
            if (picking.carrier_type != 'deutsche_post'){
                this.$('.js_de_label_download').hide()
                this.$('.js_de_label_buy').hide()
            }
            else if (picking.label_de_attach_id === false){
                this.$('.js_de_label_download').hide()
            }
            else{
                this.$('.js_de_label_buy').hide()
            }
        },
    })
}*/