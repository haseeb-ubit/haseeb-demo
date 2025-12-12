/** @odoo-module */

import snippetsEditor from "@web_editor/js/editor/snippets.editor";
import { Wysiwyg } from "@web_editor/js/wysiwyg/wysiwyg";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(snippetsEditor.SnippetsMenu.prototype, {
     _checkEditorToolbarVisibility(e) {
        super._checkEditorToolbarVisibility(...arguments);
        this.state.showToolbar = true
    },
});


patch(Wysiwyg.prototype, {
    _saveTranslationElement($el, context, withLang = true) {
        if ($el.data('oe-translation-source-sha')) {
            const $els = $el;
            const translations = {};
            translations[context.lang] = Object.assign({}, ...$els.toArray().map(
                (x) => ({
                    [$(x).data('oe-translation-source-sha')]: this._getEscapedElement($(x)).html()
                })
            ));
            return rpc('/web_editor/field/translation/update', {
                model: $els.data('oe-model'),
                record_id: [+$els.data('oe-id')],
                field_name: $els.data('oe-field'),
                translations,
            });
        } else if ($el.data('oe-model') == 'website.pagee' || $el.data('oe-news')){
            var id = $el.data('oe-id');
            var model = $el.data('oe-model');
            var field = $el.data('oe-field') || 'news_title';
            if (!id) {
                return Promise.resolve();
            }
            return this.orm.call(
                model || 'website.pagee',
                'write',
                [
                    id,
                    { [field] : $el[0]?.innerText},
                ], { context }
            );
        }else {
            var viewID = $el.data('oe-id');
            if (!viewID) {
                return Promise.resolve();
            }

            return this.orm.call(
                'ir.ui.view',
                'save',
                [
                    viewID,
                    this._getEscapedElement($el).prop('outerHTML'),
                    !$el.data('oe-expression') && $el.data('oe-xpath') || null, // Note: hacky way to get the oe-xpath only if not a t-field
                ], { context }
            );
        }
    },
    async _saveElement($el, context) {
        let result = {}
        if ($el.data('oe-model') == 'website.pagee' || $el.data('oe-news')){
            var id = $el.data('oe-id');
            var model = $el.data('oe-model');
            var field = $el.data('oe-field') || 'news_title';
            if (!id) {
                return Promise.resolve();
            }
             result =  this.orm.call(
                model || 'website.pagee',
                'write',
                [
                    id,
                    { [field] : $el[0]?.innerText},
                ], { context }
            );
        }else{
            var viewID = $el.data('oe-id');
            if (!viewID) {
                return Promise.resolve();
            }
            // remove ZeroWidthSpace from odoo field value
            // ZeroWidthSpace may be present from OdooEditor edition process
            let escapedHtml = this._getEscapedElement($el).prop('outerHTML');

             result = this.orm.call('ir.ui.view', 'save', [
                viewID,
                escapedHtml,
                !$el.data('oe-expression') && $el.data('oe-xpath') || null
            ], {
                context: {
                    ...context,
                    // TODO: Restore the delay translation feature once it's fixed,
                    //       see commit msg for more info.
                    delay_translations: false,
                },
            });
        }
        return result;
    },
});