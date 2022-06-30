odoo.define('chatter_confirm_message.composer.Basic', function (require) {
"use strict";
var BasicComposer = require('mail.composer.Basic');
var Dialog = require('web.Dialog');
const rpc = require('web.rpc');

    BasicComposer.include({
    _sendMessage: function () {
        var _super =  this._super.bind(this);
        var follower_ids =  this.__parentedParent.record.data.message_follower_ids.res_ids
        if (follower_ids.length != 0){
	         var self = this;
	         var def = rpc.query({
	                    model: 'res.partner',
	                    method: 'check_users',
	                    args: [follower_ids],
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
                    $content:  "<p>Confirm To Send Message?</p>",
                    buttons : [
                    {text: ('Close'), close: true, classes: 'btn-primary'},
                    {text: ('Confirm'), click: function () {

                        _super();
                         dialog.close()
                    },
                        classes: 'btn-primary'}
                ]
                });
        }
        else{
         _super();
        }

    },

});


});
