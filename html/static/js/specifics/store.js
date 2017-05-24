(function($)
{
    'use strict';
    $.fn.formsetInitInlineDeleteLink = function(opts)
    {
        var options = $.extend({}, $.fn.formsetInitInlineDeleteLink.defaults, opts);
        var $this = $(this);

        var totalForms = $("#id_" + options.prefix + "-TOTAL_FORMS").prop("autocomplete", "off");
        var nextIndex = parseInt(totalForms.val(), 10);

        var updateElementIndex = function(el, prefix, ndx)
        {
            var id_regex = new RegExp("(" + prefix + "-(\\d+|__prefix__))");
            var replacement = prefix + "-" + ndx;
            if ($(el).prop("for"))
            {
                $(el).prop("for", $(el).prop("for").replace(id_regex, replacement));
            }
            if (el.id)
            {
                el.id = el.id.replace(id_regex, replacement);
            }
            if (el.name)
            {
                el.name = el.name.replace(id_regex, replacement);
            }
        };
        $this.each(function(i)
        {
            var row = $(this);
            row.find("a." + options.deleteCssClass).click(function(e1)
            {
                e1.preventDefault();
                // Remove the parent form containing this button:
                row.remove();
                nextIndex -= 1;
                // If a post-delete callback was provided, call it with the deleted form:
                if (options.removed)
                {
                    options.removed(row);
                }
                $(document).trigger('formset:removed', [row, options.prefix]);
                // Update the TOTAL_FORMS form count.
                var forms = $("." + options.formCssClass);
                $("#id_" + options.prefix + "-TOTAL_FORMS").val(forms.length);

                // Also, update names and ids for all remaining form controls
                // so they remain in sequence:
                var i, formCount;
                var updateElementCallback = function()
                {
                    updateElementIndex(this, options.prefix, i);
                };
                for (i = 0, formCount = forms.length; i < formCount; i++)
                {
                    updateElementIndex($(forms).get(i), options.prefix, i);
                    $(forms.get(i)).find("*").each(updateElementCallback);
                }
            });
        });
        return this;
    };

    /* Setup plugin defaults */
    $.fn.formsetInitInlineDeleteLink.defaults =
    {
        prefix: "form",          // The form prefix for your django formset
        addText: "add another",      // Text for the add link
        deleteText: "remove",      // Text for the delete link
        addCssClass: "add-row",      // CSS class applied to the add link
        deleteCssClass: "delete-row",  // CSS class applied to the delete link
        emptyCssClass: "empty-row",    // CSS class applied to the empty row
        formCssClass: "dynamic-form",  // CSS class applied to each form in a formset
        added: null,          // Function called each time a new form is added
        removed: null          // Function called each time a form is deleted
    };

    $.fn.initInlineDeleteLink = function(options)
    {
        var $rows = $(this);
        var updateInlineLabel = function(row)
        {
            $($rows.selector).find(".inline_label").each(function(i)
            {
                var count = i + 1;
                $(this).html($(this).html().replace(/(#\d+)/g, "#" + count));
            });
        };

        $rows.formsetInitInlineDeleteLink(
        {
            prefix: options.prefix,
            addText: options.addText,
            formCssClass: "dynamic-" + options.prefix,
            deleteCssClass: "inline-deletelink",
            deleteText: options.deleteText,
            emptyCssClass: "empty-form",
            removed: updateInlineLabel
        });

        return $rows;
    };

    $(document).ready(function()
    {
        $(".js-inline-admin-formset").each(function()
        {
            var data = $(this).data(),
                inlineOptions = data.inlineFormset;
            $(inlineOptions.name + "-group .inline-related").initInlineDeleteLink(inlineOptions.options);
        });
    });
})(django.jQuery);
