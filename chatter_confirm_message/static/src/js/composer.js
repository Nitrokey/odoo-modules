odoo.define('chatter_confirm_message.composer.Basic', function (require) {
"use strict";
var BasicComposer = require('mail.composer.Basic');
var Dialog = require('web.Dialog');
var translation = require('web.translation');
var _t = translation._t;
const rpc = require('web.rpc');

    BasicComposer.include({
    _sendMessage: function () {
        var _super =  this._super.bind(this);
        var follower_ids = null;
        var rec_id = null;
        var model = null;
        if (this.__parentedParent.record &&	this.options.isLog == false){
            var follower_ids =  this.__parentedParent.record.data.message_follower_ids.res_ids
        }
        if(!follower_ids && this.options.isLog != true && 'action' in this.__parentedParent && this.__parentedParent.action.display_name == 'Discuss'){
            var rec_id = this.__parentedParent._selectedMessage._documentID
            var model = this.__parentedParent._selectedMessage._documentModel
        }
         if (follower_ids != null || rec_id){
	         var self = this;
	         var def = rpc.query({
	                    model: 'res.partner',
	                    method: 'check_users',
	                    args: [follower_ids, rec_id, model],
	                    }).then(function (resposne) {
	                        if (resposne == true){
	                            dialog.open()
	                        }
	                        else{
	                        	_super();
	                        }
        	});
        	var dialog = new Dialog(self, {
                    title:('Confirmation For Chatter'),
                    size: 'medium',
                    $content: (_t("<p>Your message will be sent to external partners (e.g. customers).</p>")),
                    buttons : [
                    {text: (_t('Send')), click: function () {

                        _super();
                         dialog.close()
                    },
                        classes: 'btn-primary'},
                    {text: (_t('Cancel')), close: true, classes: 'btn-primary'}
                ]
                });
        }
        else{
         _super();
        }

    },

});


});
