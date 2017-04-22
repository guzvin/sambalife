/*global DateTimeShortcuts, SelectFilter*/
/**
 * Django admin inlines
 *
 * Based on jQuery Formset 1.1
 * @author Stanislaus Madueke (stan DOT madueke AT gmail DOT com)
 * @requires jQuery 1.2.6 or later
 *
 * Copyright (c) 2009, Stanislaus Madueke
 * All rights reserved.
 *
 * Spiced up with Code from Zain Memon's GSoC project 2009
 * and modified for Django by Jannis Leidel, Travis Swicegood and Julien Phalip.
 *
 * Licensed under the New BSD License
 * See: http://www.opensource.org/licenses/bsd-license.php
 */
(function($) {
    'use strict';
    $.fn.formset = function(opts) {
        var options = $.extend({}, $.fn.formset.defaults, opts);
        var $this = $(this);
        var $parent = $this.parent();
        var updateElementIndex = function(el, prefix, ndx) {
            var id_regex = new RegExp("(" + prefix + "-(\\d+|__prefix__))");
            var replacement = prefix + "-" + ndx;
            if ($(el).prop("for")) {
                $(el).prop("for", $(el).prop("for").replace(id_regex, replacement));
            }
            if (el.id) {
                el.id = el.id.replace(id_regex, replacement);
            }
            if (el.name) {
                el.name = el.name.replace(id_regex, replacement);
            }
        };
        var totalForms = $("#id_" + options.prefix + "-TOTAL_FORMS").prop("autocomplete", "off");
        var nextIndex = parseInt(totalForms.val(), 10);
        var maxForms = $("#id_" + options.prefix + "-MAX_NUM_FORMS").prop("autocomplete", "off");
        // only show the add button if we are allowed to add more items,
        // note that max_num = None translates to a blank string.
        var showAddButton = maxForms.val() === '' || (maxForms.val() - totalForms.val()) > 0;
        $this.each(function(i) {
            var row = $(this).not("." + options.emptyCssClass);
            row.addClass(options.formCssClass);
            row.find("a." + options.deleteCssClass).click(function(e1) {
                e1.preventDefault();
                // Remove the parent form containing this button:
                row.remove();
                nextIndex -= 1;
                // If a post-delete callback was provided, call it with the deleted form:
                if (options.removed) {
                    options.removed(row);
                }
                $(document).trigger('formset:removed', [row, options.prefix]);
                // Update the TOTAL_FORMS form count.
                var forms = $("." + options.formCssClass);
                $("#id_" + options.prefix + "-TOTAL_FORMS").val(forms.length);
                // Show add button again once we drop below max
                if ((maxForms.val() === '') || (maxForms.val() - forms.length) > 0) {
                    addButton.parent().show();
                }
                // Also, update names and ids for all remaining form controls
                // so they remain in sequence:
                var i, formCount;
                var updateElementCallback = function() {
                    updateElementIndex(this, options.prefix, i);
                };
                for (i = 0, formCount = forms.length; i < formCount; i++) {
                    updateElementIndex($(forms).get(i), options.prefix, i);
                    $(forms.get(i)).find("*").each(updateElementCallback);
                }
            });
        });
        if ($this.length && showAddButton) {
            var addButton = $('a.' + options.addCssClass);
            addButton.click(function(e) {
                e.preventDefault();
                var template = $("#" + options.prefix + "-empty");
                var row = template.clone(true);

                row.removeClass(options.emptyCssClass)
                .addClass(options.formCssClass)
                .attr("id", options.prefix + "-" + nextIndex);

                row.find("*").each(function() {
                    updateElementIndex(this, options.prefix, totalForms.val());
                });
                // Insert the new form when it has been fully edited
                row.insertBefore($(template));
                // Update number of total forms
                $(totalForms).val(parseInt(totalForms.val(), 10) + 1);
                nextIndex += 1;
                // Hide add button in case we've hit the max, except we want to add infinitely
                if ((maxForms.val() !== '') && (maxForms.val() - totalForms.val()) <= 0) {
                    addButton.parent().hide();
                }
                // The delete button of each row triggers a bunch of other things
                row.find("a." + options.deleteCssClass).click(function(e1) {
                    e1.preventDefault();
                    // Remove the parent form containing this button:
                    row.remove();
                    nextIndex -= 1;
                    // If a post-delete callback was provided, call it with the deleted form:
                    if (options.removed) {
                        options.removed(row);
                    }
                    $(document).trigger('formset:removed', [row, options.prefix]);
                    // Update the TOTAL_FORMS form count.
                    var forms = $("." + options.formCssClass);
                    $("#id_" + options.prefix + "-TOTAL_FORMS").val(forms.length);
                    // Show add button again once we drop below max
                    if ((maxForms.val() === '') || (maxForms.val() - forms.length) > 0) {
                        addButton.parent().show();
                    }
                    // Also, update names and ids for all remaining form controls
                    // so they remain in sequence:
                    var i, formCount;
                    var updateElementCallback = function() {
                        updateElementIndex(this, options.prefix, i);
                    };
                    for (i = 0, formCount = forms.length; i < formCount; i++) {
                        updateElementIndex($(forms).get(i), options.prefix, i);
                        $(forms.get(i)).find("*").each(updateElementCallback);
                    }
                });
                // If a post-add callback was supplied, call it with the added form:
                if (options.added) {
                    options.added(row);
                }
                $(document).trigger('formset:added', [row, options.prefix]);
            });
        }
        return this;
    };

    /* Setup plugin defaults */
    $.fn.formset.defaults = {
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

    // Stacked inlines ---------------------------------------------------------
    $.fn.stackedFormset = function(options) {
        var $rows = $(this);
        var updateInlineLabel = function(row) {
            $($rows.selector).find(".inline_label").each(function(i) {
                var count = i + 1;
                $(this).html($(this).html().replace(/(#\d+)/g, "#" + count));
            });
        };

        var reinitDateTimeShortCuts = function() {
            // Reinitialize the calendar and clock widgets by force, yuck.
            if (typeof DateTimeShortcuts !== "undefined") {
                $(".datetimeshortcuts").remove();
                DateTimeShortcuts.init();
            }
        };

        var updateSelectFilter = function() {
            // If any SelectFilter widgets were added, instantiate a new instance.
            if (typeof SelectFilter !== "undefined") {
                $(".selectfilter").each(function(index, value) {
                    var namearr = value.name.split('-');
                    SelectFilter.init(value.id, namearr[namearr.length - 1], false);
                });
                $(".selectfilterstacked").each(function(index, value) {
                    var namearr = value.name.split('-');
                    SelectFilter.init(value.id, namearr[namearr.length - 1], true);
                });
            }
        };

        var initPrepopulatedFields = function(row) {
            row.find('.prepopulated_field').each(function() {
                var field = $(this),
                    input = field.find('input, select, textarea'),
                    dependency_list = input.data('dependency_list') || [],
                    dependencies = [];
                $.each(dependency_list, function(i, field_name) {
                    dependencies.push('#' + row.find('.form-row .field-' + field_name).find('input, select, textarea').attr('id'));
                });
                if (dependencies.length) {
                    input.prepopulate(dependencies, input.attr('maxlength'));
                }
            });
        };

        $rows.formset({
            prefix: options.prefix,
            addText: options.addText,
            formCssClass: "dynamic-" + options.prefix,
            deleteCssClass: "inline-deletelink",
            deleteText: options.deleteText,
            emptyCssClass: "empty-form",
            removed: updateInlineLabel,
            added: function(row) {
                initPrepopulatedFields(row);
                reinitDateTimeShortCuts();
                updateSelectFilter();
                updateInlineLabel(row);
            }
        });

        return $rows;
    };

    $(document).ready(function() {
        $(".js-inline-admin-formset").each(function() {
            var data = $(this).data(),
                inlineOptions = data.inlineFormset;
            switch(data.inlineType) {
            case "stacked":
                $(inlineOptions.name + "-group .inline-related").stackedFormset(inlineOptions.options);
                break;
            }
        });
    });
})(jQuery);
