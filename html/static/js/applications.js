// Agency Theme JavaScript

(function($)
{
    'use strict';
    function getCookie(name)
    {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '')
        {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++)
            {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '='))
                {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function csrfSafeMethod(method)
    {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    $.ajaxSetup(
    {
        beforeSend: function(xhr, settings)
        {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain)
            {
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    $(document).ajaxError(function( event, jqXHR, settings, thrownError )
    {
        if(jqXHR.responseJSON && jqXHR.responseJSON.terms_and_conditions)
        {
            $('#terms_conditions').modal('show');
        }
    });

    // jQuery for page scrolling feature - requires jQuery Easing plugin
    $('a.page-scroll').bind('click', function(event)
    {
        var $anchor = $(this);
        $('html, body').stop().animate(
        {
            scrollTop: ($($anchor.attr('href')).offset().top - 50)
        }, 1250, 'easeInOutExpo');
        event.preventDefault();
    });

    if($('body.index').scrollspy)
    {
        // Highlight the top nav as scrolling occurs
        $('body.index').scrollspy(
        {
            target: '.navbar-fixed-top',
            offset: 51
        });
    }

    if($('body.index-home #mainNav').affix)
    {
        // Offset for Main Navigation
        $('body.index-home #mainNav').affix(
        {
            offset:
            {
                top: 100
            }
        });
    }

    $('.mudar-status').click(function()
    {
        var elem = $(this).parent('td').find('.contem-status');
        if(elem.is(':visible'))
            elem.hide();
        else
            elem.show();
    });
    
    $('.fechar').click(function()
    {
        $(this).closest('.contem-status').hide();
    });
    
    if($.datepicker){
        $.datepicker.regional['pt-BR'] =
        {
            closeText: 'Fechar',
            prevText: '&#x3c;Anterior',
            nextText: 'Pr&oacute;ximo&#x3e;',
            currentText: 'Hoje',
            monthNames: ['Janeiro','Fevereiro','Mar&ccedil;o','Abril','Maio','Junho',
            'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'],
            monthNamesShort: ['Jan','Fev','Mar','Abr','Mai','Jun',
            'Jul','Ago','Set','Out','Nov','Dez'],
            dayNames: ['Domingo','Segunda-feira','Ter&ccedil;a-feira','Quarta-feira','Quinta-feira','Sexta-feira','Sabado'],
            dayNamesShort: ['Dom','Seg','Ter','Qua','Qui','Sex','Sab'],
            dayNamesMin: ['Dom','Seg','Ter','Qua','Qui','Sex','Sab'],
            weekHeader: 'Sm',
            dateFormat: 'dd/mm/yy',
            firstDay: 0,
            isRTL: false,
            showMonthAfterYear: false,
            yearSuffix: ''
        };

        $.datepicker.setDefaults($.datepicker.regional[gettext('en-US')]);

        $( ".datepicker" ).datepicker();
    }

    if($("[data-toggle='tooltip']").tooltip)
    {
        $("[data-toggle='tooltip']").tooltip(
        {
            placement : 'top'
        });
    }

    if($.validator)
    {
        $.validator.methods.passwordFormat = function( value, element )
        {
            return this.optional( element ) || (/[A-Z]/.test(value)
                                                && /[a-z]/.test(value)
                                                && /\d/.test(value)
                                                && /[^a-zA-Z\d]/.test(value));
        };

        $.validator.addMethod('positiveNumber', function (value, element)
        {
            if (this.optional(element))
            {
                return true;
            }
            try
            {
                if(parseFloat(value) > 0)
                {
                    return !isNaN(value);
                }
            }
            catch (err)
            {}
            return false;
        });

        if($.datepicker)
        {
            $.validator.addMethod('date', function (value, element)
            {
                if (this.optional(element))
                {
                    return true;
                }
                var valid = true;
                try
                {
                    $.datepicker.parseDate(gettext('mm/dd/yy'), value);
                }
                catch (err)
                {
                    valid = false;
                }
                return valid;
            });
            $.validator.addMethod('dateLessThanOrEqualNow', function (value, element)
            {
                if (this.optional(element))
                {
                    return true;
                }
                var valid = true;
                try
                {
                    return $.datepicker.parseDate(gettext('mm/dd/yy'), value) <= new Date();
                }
                catch (err)
                {
                    valid = false;
                }
                return valid;
            });
            $.validator.addMethod('dateGreaterThan', function (value, element, params)
            {
                if (this.optional(element))
                {
                    return true;
                }
                var valid = true;
                try
                {
                    var dateToCompare = $.datepicker.parseDate(gettext('mm/dd/yy'), $(params[0]).val());
                    if(!dateToCompare)
                    {
                        throw 'null';
                    }
                    try
                    {
                        return $.datepicker.parseDate(gettext('mm/dd/yy'), value) > dateToCompare;
                    }
                    catch (err)
                    {
                        valid = false;
                    }
                }
                catch (err)
                {
                    valid = false;
                }
                return valid;
            } , $.validator.format(gettext('Please enter a date greater than {1}.')));
            $.validator.addMethod('productsNotEmpty', function (value, element)
            {
                return $(element).val() === '1';
            });
        }

        $.extend(
            $.validator.messages,
            {
                required: gettext('Required field.'),
                minlength: gettext('Please enter at least 6 characters.'),
                equalTo: gettext('Please enter the same value again.'),
                passwordFormat: gettext('See instructions for valid format.'),
                email: gettext('Please enter a valid email address.'),
                date: gettext('Please enter a valid date.'),
                dateLessThanOrEqualNow: gettext('Please enter a date less than or equal to today.'),
                positiveNumber: gettext('Please enter a number greater than zero.'),
                productsNotEmpty: gettext('You must add products to this shipment.'),
            }
        );
    }

    if($('form#form-add-user')[0])
    {
        $('button#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
        });

        $('form#form-add-user').validate(
        {
            rules:
            {
                first_name: { required: true },
                last_name: { required: true },
                email: { required: true },
                doc_number: { required: true },
                cell_phone: { required: true },
                country: { required: true },
                address_1: { required: true },
                city: { required: true },
                state: { required: true },
                zipcode: { required: true },
                password:
                {
                    required: true,
                },
                password_confirmation:
                {
                    required: true,
                    equalTo: '#senha'
                },
                terms: { required: true },
            },
            errorPlacement: function(error, element)
            {
                if (element.attr('name') == 'terms')
                {
                    error.insertAfter(element.parent());
                }
                else
                {
                    error.insertAfter(element);
                }
            },
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('button#send-btn').removeClass('nosubmit');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });
    }

    if($('form#form-login')[0])
    {
        $('input#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
            $('form#form-login').attr('action', '/' + gettext('en') + gettext('/login') + '/');
        });

        $('a#forgot-password-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
            $('form#form-login').attr('action', '/' + gettext('en') + gettext('/user/password/forgot/'));
            $('form#form-login').submit();
        });

        $('form#form-login').validate(
        {
            errorPlacement: function(error, element)
            {
                var breakLine = $('<br></br>');
                breakLine.insertAfter(element);
                error.insertAfter(breakLine);
                breakLine.clone().insertAfter(error);
            },
            rules:
            {
                login: { required: true },
                password:
                {
                    required:
                    {
                        depends: function(element)
                        {
                          return $('form#form-login').attr('action') === '/' + gettext('en') + gettext('/login') + '/';
                        }
                    },
                },
            },
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('input#send-btn').removeClass('nosubmit');
                $('a#forgot-password-btn').removeClass('nosubmit');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });
    }

    if($('form#form-reset-password')[0])
    {
        $('button#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
        });

        $('form#form-reset-password').validate(
        {
            rules:
            {
                email: { required: true },
                password:
                {
                    required: true,
                },
                password_confirmation:
                {
                    required: true,
                    equalTo: '#senha'
                },
            },
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('button#send-btn').removeClass('nosubmit');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });
    }

    if($('form#form-add-product')[0])
    {
        $('button#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
        });

        $('form#form-add-product').validate(
        {
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('button#send-btn').removeClass('nosubmit');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });
        $('.name_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true
            });
        });
        $('.quantity_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        });
        $('.quantity_partial_validate').each(function ()
        {
            $(this).rules('add',
            {
                positiveNumber: true,
            });
        });
        $('.stock_type_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true
            });
        });
        $('.send_date_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                date: true,
                dateLessThanOrEqualNow: true,
            });
        });
        $('.edd_date_validate').each(function ()
        {
            $(this).rules('add',
            {
                date: true,
                dateGreaterThan: ['.send_date_validate', gettext('Purchase date')],
            });
        });
        $('.best_before_validate').each(function ()
        {
            $(this).rules('add',
            {
                date: true,
            });
        });
        $('.condition_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
    }

    $('.send-btn-async').click(function(e)
    {
        var form = $(this).closest('form.form-change-status');
        var pid = form.find('input.product-id').val();
        if(form.attr('id').split('-')[3] === pid)
        {
            var radioChecked = form.find('input:radio:checked');
            if(radioChecked[0])
            {
                var tr = form.closest('tr');
                var quantityColumn = tr.find('td.row-quantity');
                var pickTicketColumn = tr.find('td.row-pick-ticket-display');
                var inputPartial = tr.find('input.row-qty-partial');
                var currentPartial = inputPartial.data('current-partial');
                var newPartialValue = inputPartial.val();
                var inputBestBefore = tr.find('input.row-best-before');
                var currentBestBefore = inputBestBefore.data('best-before')
                var newBestBeforeValue = inputBestBefore.val();
                var selectActualCondition = tr.find('select.row-actual-condition');
                var currentActualCondition = selectActualCondition.data('actual-condition')
                var newActualConditionValue = selectActualCondition.val();
                var inputConditionComments = tr.find('input.row-condition-comments');
                var currentConditionComments = inputConditionComments.data('condition-comments')
                var newConditionCommentsValue = inputConditionComments.val();

                var inputPickTicket = tr.find('input.row-pick-ticket');
                var currentPickTicket = inputPickTicket.data('pick-ticket')
                var newPickTicketValue = inputPickTicket.val();

                var checkedValue = radioChecked.val();
                var currentValue = radioChecked.data('current-status');
                if(''+checkedValue !== ''+currentValue || ''+currentPartial !== ''+newPartialValue || ''+currentBestBefore != ''+newBestBeforeValue
                || ''+currentActualCondition != ''+newActualConditionValue || ''+currentConditionComments != ''+newConditionCommentsValue
                || ''+currentPickTicket != ''+newPickTicketValue)
                {
                    var $this = $(this);
                    if($this.hasClass('nosubmit'))
                    {
                        e.preventDefault();
                        return false;
                    }
                    $this.addClass('nosubmit');
                    $('.loading').show();
                    $.ajax(
                    {
                        method: 'PUT',
                        url: '/' + gettext('en') + '/product/edit/status/' + pid + '.json',
                        data: form.serialize()
                    })
                    .done(function( obj )
                    {
                        $('span#product-status-display-'+obj.product.id).text(obj.product.status_display);
                        form.find('input:radio').data('current-status', obj.product.status);
                        inputPartial.data('current-partial', obj.product.quantity_partial);
                        inputBestBefore.data('best-before', obj.product.best_before);
                        selectActualCondition.data('actual-condition', obj.product.actual_condition);
                        inputConditionComments.data('condition-comments', obj.product.condition_comments);
                        inputPickTicket.data('pick-ticket', obj.product.pick_ticket);
                        if(obj.product.show_check && obj.product.status === SHIPMENT_STATUS_IN_STOCK && obj.product.quantity >= 0)
                        {
                            var checkColumn = $('span#product-status-display-'+obj.product.id).closest('td').next();
                            if(!checkColumn.find('input[type="checkbox"]')[0])
                            {
                                var checkbox = $('<input type="checkbox" name="shipment_product" value="' + obj.product.id + '" id="shipment-' + obj.product.id + '" class="shipment-product" />');
                                checkColumn.append(checkbox);
                            }
                        }
                        else
                        {
                            $('span#product-status-display-'+obj.product.id).closest('td').next()[0].innerHTML = '';
                        }
                        var qtyInfo = obj.product.quantity;
                        if(parseInt(obj.product.quantity_partial) && !isNaN(obj.product.quantity_partial) && obj.product.quantity !== obj.product.quantity_partial)
                        {
                            qtyInfo += ' ('+obj.product.quantity_partial+')';
                        }
                        quantityColumn.find('span.row-quantity-display')[0].innerHTML = qtyInfo;
                        var bestBefore = obj.product.best_before;
                        var rowBestBefore = quantityColumn.find('span.row-bestbefore-display');
                        if(bestBefore !== '')
                        {
                            if(rowBestBefore[0])
                            {
                                rowBestBefore[0].innerHTML = '<br>' + gettext('Expiration date') + ':<br>' + bestBefore;
                            }
                            else
                            {
                                quantityColumn.append($('<span class="row-bestbefore-display"><br>' + gettext('Expiration date') + ':<br>' + bestBefore + '</span>'));
                            }
                        }
                        else
                        {
                            if(rowBestBefore[0])
                            {
                                rowBestBefore.remove();
                            }
                        }
                        var pickTicket = obj.product.pick_ticket;
                        $('span.help.fa-thumb-tack').remove();
                        if(pickTicket !== '')
                        {
                            pickTicketColumn.append($('<span class="help help-tooltip fa fa-thumb-tack" title="' + gettext('Pick ticket') + ': ' + pickTicket + '"></span>'));
                        }
                        form.closest('.contem-status').hide();
                    })
                    .fail(function(jqXHR, textStatus, errorThrown)
                    {
                        if(jqXHR.responseJSON && jqXHR.responseJSON.terms_and_conditions)
                        {
                            return;
                        }
                        alert(jqXHR.responseJSON.error);
                    })
                    .always(function()
                    {
                        $('.loading').hide();
                        $this.removeClass('nosubmit');
                    });
                }
            }
        }
        return false;
    });

    $('.send-btn-delete, #cancel-btn').click(function()
    {
        $('#confirmacao-exclusao').modal('show');
    });

    $('#btn-explicacao').click(function()
    {
        $('#assinantes-modal').modal('show');
    });

    $('.open-adress').click(function()
    {
        $('#box-adress').modal('show');
    });

    if($('#form-archive-shipment')[0])
    {
        if($('#archive-btn')[0])
        {
            $('#archive-btn').click(function()
            {
                $('.loading').show();
                $('#form-archive-shipment').submit();
            });
        }
        else if($('#restore-btn')[0])
        {
            $('#restore-btn').click(function()
            {
                $('.loading').show();
                $('#form-archive-shipment').submit();
            });
        }
    }

    if($('#form-standby-shipment')[0])
    {
        if($('#standby-btn')[0] || $('#standby-btn-remove')[0])
        {
            $("#standby-btn").click(function(){
                $('#modal-standby').modal('show');
            });
            $("#standby-btn-remove").click(function(){
                $('.loading').show();
                $('#form-standby-shipment').submit();
            });
            $('#standby-btn-save').click(function()
            {
                $('.loading').show();
                $('#standby_shipment_reason').val($('#modal_standby_shipment_reason').val());
                $('#form-standby-shipment').submit();
            });
        }
    }

    $('.privatebtn').click(function()
    {
        $('#portfolioModal1').modal('show');
    });

    $('#privatebtn').click(function()
    {
        $('#portfolioModal1').modal('show');
    });

    if($('#form-add-shipment')[0])
    {
        var shipmentProducts = sessionStorage.getItem('shipment_products');
        if(!shipmentProducts)
        {
            shipmentProducts = '{}'
        }
        shipmentProducts = JSON.parse(shipmentProducts);
        $('.shipment-product').each(function()
        {
            if(shipmentProducts['p' + $(this).val()])
            {
                this.checked = true;
            }
            else
            {
                this.checked = false;
            }
        });

        var shipmentForm = $('#form-add-shipment');
        $('.shipment-product').change(function()
        {
            if(this.checked)
            {
                shipmentProducts['p' + $(this).val()] = $(this).val();
            }
            else
            {
                delete shipmentProducts['p' + $(this).val()];
            }
            sessionStorage.setItem('shipment_products', JSON.stringify(shipmentProducts));
        });
        $('#btn-create-shipment').click(function()
        {
            $('#modal-whaz').modal('show');
        });
        $('#btn-add-shipment, #btn-add-merchant-shipment, #btn-create-shipment-0').click(function()
        {
            var get = false;
            for(var shipmentProduct in shipmentProducts)
            {
                var checkedProduct = $('<input type="hidden" name="shipment_product"></input>');
                checkedProduct.val(shipmentProducts[shipmentProduct]);
                checkedProduct.appendTo(shipmentForm);
                get = false;
            }
            var selectedCollaborator = $('<input type="hidden" name="shipment_collaborator"></input>');
            selectedCollaborator.val($('select#collaborator-filter').val());
            selectedCollaborator.appendTo(shipmentForm);

            if(get)
            {
                window.location.href = $(this).data('action-url');
            }
            else
            {
//                sessionStorage.removeItem('shipment_products');
                shipmentForm.attr('action', $(this).data('action-url'));
                shipmentForm.submit();
            }
        });
        $('#btn-save-user-amz-store').click(function()
        {
            $.ajax(
            {
                method: 'POST',
                url: '/' + gettext('en') + '/user/amz_store_name/',
                data: $('#form-edit-user-amz-store').serialize(),
            })
            .done(function()
            {
                $('#anchor-user-amz-store').click();
            });
        });
    }
    else
    {
//        sessionStorage.removeItem('shipment_products');
    }

    if($('form#form-save-shipment')[0])
    {
        $('button#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
        });

        $('form#form-save-shipment').validate(
        {
            ignore: '#id_product_set-__prefix__-quantity, #hidden_id_product_set-__prefix__-quantity, #id_warehouse_set-__prefix__-name',
            submitHandler: function(form)
            {
                $('.loading').show();
                sessionStorage.removeItem('shipment_products');
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('button#send-btn').removeClass('nosubmit');
                $('.send-btn-error').remove();
                $('<label class="error send-btn-error" for="send-btn">' + gettext('Fix the errors above and try again.') + '</label>').insertAfter('button#send-btn');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });

        window.addRule = function(element, rules)
        {
            element.rules('add', rules);
        }

        $('.quantity_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        });
        $('.pdf_1-validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
        $('.warehouse_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
        $('.products_validate').each(function ()
        {
            $(this).rules('add',
            {
                productsNotEmpty: true,
            });
        });
    }

    if($('form.form-filter')[0])
    {
        $('a.order-by').click(function(e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
            var data = $(this).data();
            var orderBy = $('input#order-by');
            if(orderBy[0])
            {
                orderBy.val(data.order);
            }
            else
            {
                var hidden = $('<input type="hidden" name="order" value="' + data.order + '" id="order-by" />');
                $('form.form-filter').append(hidden);
            }
            $('form.form-filter').submit();
        });
        $('a.pagination-page').click(function(e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
            var data = $(this).data();
            var selectedPage = $('input#selected-page');
            if(selectedPage[0])
            {
                selectedPage.val(data.page);
            }
            else
            {
                var hidden = $('<input type="hidden" name="page" value="' + data.page + '" id="selected-page" />');
                $('form.form-filter').append(hidden);
            }
            $('form.form-filter').submit();
        });
        $('form.form-filter').find('button[type="submit"]').click(function(e)
        {
            e.preventDefault();
            if($(this).hasClass('nosubmit'))
            {
                return false;
            }
            $(this).addClass('nosubmit');
            var selectedPage = $('input#selected-page');
            if(selectedPage[0])
            {
                selectedPage.remove();
            }
            var orderBy = $('input#order-by');
            if(orderBy[0])
            {
                orderBy.remove();
            }
            $('form.form-filter').submit();
        });
    }

    if($('form#form-add-package')[0])
    {
        $('a#change-btn-status-forward').on('click', function (e)
        {
            if($('.services-validation').valid())
            {
                return true;
            }
            $('.send-btn-error').remove();
            $('<label class="error send-btn-error" for="send-btn">' + gettext('Fix the errors above and try again.') + '</label>').insertAfter('a#change-btn-status-forward');
            return false;
        });

        $('a#send-btn-1').on('click', function (e)
        {
            e.preventDefault();
            if($(this).hasClass('nosubmit'))
            {
                return false;
            }
            $(this).addClass('nosubmit');
            $('form#form-add-package').submit();
        });

        $('form#form-add-package').validate(
        {
            ignore: '#id_package_set-__prefix__-warehouse, #id_package_set-__prefix__-height, #id_package_set-__prefix__-length, #id_package_set-__prefix__-width, #id_package_set-__prefix__-weight',
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('a#send-btn-1').removeClass('nosubmit');
                $('.send-btn-error').remove();
                $('<label class="error send-btn-error" for="send-btn">' + gettext('Fix the errors above and try again.') + '</label>').insertAfter('a#send-btn-1');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });

        window.addRule = function(element, rules)
        {
            element.rules('add', rules);
        }

        $('input.required-validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
        $('input.required-number-validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        });
    }

    $('a.delete-product-shipment').each(function()
    {
        $(this).click(function(e)
        {
            e.preventDefault();
            var tr = $(this).closest('tr');
            $('#delete_product_shipment_id').val($(this).data('delete-product-shipment-id'));
            $('#delete_product_product_id').val($(this).data('delete-product-product-id'));
            var form = $('#delete_product_product_id').closest('form');
            $.ajax(
            {
                method: 'DELETE',
                url: '/' + gettext('en') + '/shipment/delete/product.json',
                data: form.serialize(),
                statusCode:
                {
                    400: function(jqXHR, textStatus, errorThrown)
                    {
                        if(jqXHR.responseJSON && jqXHR.responseJSON.terms_and_conditions)
                        {
                            return;
                        }
                        var body = gettext('Sorry, but there seems to be some inconsistencies. Please reload the page and try again.');
                        assembleModal(gettext('Error'), body);
                    },
                    403: function()
                    {
                        var body = gettext('Access denied');
                        assembleModal(gettext('Error'), body);
                    },
                    500: function()
                    {
                        var body = gettext('Sorry, we are unable to process your operation. Please reload the page and try again.');
                        assembleModal(gettext('Error'), body);
                    }
                }
            })
            .done(function( obj )
            {
                if(obj.redirect)
                {
                    window.location.href = obj.redirect;
                    $('.loading').show();
                    return;
                }
                tr.remove();
                $('#totalProducts')[0].innerHTML = obj.items;
                var totalCost = $('#totalCost')[0];
                if(totalCost)
                {
                    totalCost.innerHTML = obj.cost;
                }
            })
            .always(function()
            {
                $('#delete_product_shipment_id').val('');
                $('#delete_product_product_id').val('');
            });
        });
    });

    if($('form#form-upload-file')[0])
    {
        $('a#send-btn-3').on('click', function (e)
        {
            e.preventDefault();
            if($(this).hasClass('nosubmit'))
            {
                return false;
            }
            $(this).addClass('nosubmit');
            $('form#form-upload-file').submit();
        });

        $('form#form-upload-file').validate(
        {
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('a#send-btn-3').removeClass('nosubmit');
                $('a#send-btn-5').removeClass('nosubmit');
                $('.loading').hide();
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });
        if($('input[type="hidden"][name="add_package_file"]')[0] && $('input[type="hidden"][name="edit_package_warehouse"]')[0] === undefined)
        {
            $('.pdf_2-validate').each(function ()
            {
                $(this).rules('add',
                {
                    required: true,
                });
            });
        }
    }
    if($('input#payment_button')[0])
    {
        $('input#payment_button').click(function(e)
        {
            var $this = $(this);
            if($this.data('type') === 1)
            {
                $('.fba-text').show();
                $('.fbm-text').hide();
                $('.shipment-text').hide();
            }
            else if($this.data('type') === 2)
            {
                $('.fba-text').hide();
                $('.fbm-text').show();
                $('.shipment-text').hide();
            }
            else if($this.data('type') === 3)
            {
                $('.fba-text').hide();
                $('.fbm-text').hide();
                $('.shipment-text').show();
            }
            else
            {
                $('.fba-text').hide();
                $('.fbm-text').hide();
                $('.shipment-text').hide();
            }

            $('#modal-compra').modal('show');
        });

        if($('#btn-confirmar-modal-compra')[0])
        {
            $('#btn-confirmar-modal-compra').click(function(e)
            {
                e.preventDefault();
                var $this = $('input#payment_button');
                $.ajax(
                {
                    method: 'GET',
                    url: '/' + gettext('en') + '/' + $this.data('origin') + '/pay/' + $this.data('generic'),
                    statusCode:
                    {
                        400: function(jqXHR, textStatus, errorThrown)
                        {
                            if(jqXHR.responseText)
                            {
                                $('html')[0].innerHTML = jqXHR.responseText;
                                return;
                            }
                            var body = gettext('Sorry, but this item is unavailable.');
                            assembleModal(gettext('Error'), body);
                        },
                        403: function()
                        {
                            var body = gettext('Access denied');
                            assembleModal(gettext('Error'), body);
                        },
                        500: function()
                        {
                            var body = gettext('Sorry, we are unable to process your operation. Please reload the page and try again.');
                            assembleModal(gettext('Error'), body);
                        }
                    }
                })
                .done(function( obj )
                {
                    if(obj.redirect)
                    {
                        window.location.href = obj.redirect;
                        return;
                    }
                    if(obj.modal)
                    {
                        $('#modal-store-subscribe').modal('show');
                        return;
                    }
                    var paymentFormArea = $('<span id="payment-form-area"></span>').append($(obj));
                    paymentFormArea.insertAfter($this);
                    var paymentFormArea = $('span#payment-form-area');
                    paymentFormArea.find('form').submit();
                    paymentFormArea.remove();
                });
            });
        }
    }

    $('a.not-subscriber').click(function(e)
    {
        e.preventDefault();
        $('#modal-store-subscribe').modal('show');
        return false;
    });

    if($('a#send-btn-final')[0])
    {
        $('a#send-btn-final').on('click', function (e)
        {
            e.preventDefault();
            $('#send-shipment-confirmation').modal('show');
            return false;

        });
    }
    if($('button#send-btn-final-confirmation')[0])
    {
        $('button#send-btn-final-confirmation').on('click', function (e)
        {
            e.preventDefault();
            if($(this).hasClass('nosubmit'))
            {
                return false;
            }
            $(this).addClass('nosubmit');
            $('.loading').show();
            $('form#form-upload-file').append('<input type="hidden" name="complete_shipment" value="1"></input>');
            $('form#form-upload-file').submit();
        });
    }
    if($('a#send-btn-5')[0])
    {
        $('a#send-btn-5').on('click', function (e)
        {
            e.preventDefault();
            if($(this).hasClass('nosubmit'))
            {
                return false;
            }
            $(this).addClass('nosubmit');
            $('.loading').show();
            $('form#form-upload-file').submit();
        });
    }

    if($('textarea.wh-ck')[0])
    {
        $('textarea.wh-ck').each(function ()
        {
            CKEDITOR.replace($(this).attr('id'),
            {
                customConfig: 'my_config.js'
            });
        });
    }

    function assembleModal(title, body)
    {
        $('#confirmacao').find('div.modal-content h4.modal-title')[0].innerHTML = title;
        var modalBody = $('#confirmacao').find('div.modal-content div.modal-body');
        modalBody[0].innerHTML = '';
        modalBody.append($('<p>' + body + '</p>'));
        $('#confirmacao').modal('show');
    }

    $('#assinatura-confirm').modal('show');

    $('#contato-popup-link').click(function(){
        $('#contato-modal').modal('show');
    });


    if($('#terms_conditions')[0])
    {
        $('#terms_conditions').modal('show');
        if($('#terms-conditions-acceptance')[0])
        {
            $('#terms-conditions-acceptance').click(function()
            {
                $.ajax(
                {
                    method: 'POST',
                    url: '/' + gettext('en') + '/user/accept_terms/',
                })
                .done(function()
                {
                    $('#terms_conditions').modal('hide');
                });
                return false;
            });
        }
    }

    if($('#product_delete_error')[0])
    {
        $('#product_delete_error').modal('show');
    }

    if($('#contactus-form')[0])
    {
        var form = $('form#contactForm');
        $('#contactus-form').click(function (e)
        {
            var $this = $(this);
            if($this.hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $this.addClass('nosubmit');
            $('#contact-us-feedback').prop('class', '');
            $('#contact-us-feedback')[0].innerHTML = '';
            $('.loading').show();

            $.ajax(
            {
                method: 'GET',
                url: '/' + gettext('en') + '/touch/'
            }).done(function( obj )
            {
                console.log('done');
                $.ajax(
                {
                    method: 'POST',
                    url: '/' + gettext('en') + '/contactus/',
                    data: form.serialize()
                })
                .done(function( obj )
                {
                    form[0].reset();
                    $('#contact-us-feedback').prop('class', 'contact-us-success');
                    $('#contact-us-feedback')[0].innerHTML = gettext('Your message has been sent. Thank you for your contact.');
                })
                .fail(function(jqXHR, textStatus, errorThrown)
                {
                    $('#contact-us-feedback').prop('class', 'contact-us-failure');
                    $('#contact-us-feedback')[0].innerHTML = gettext('Sorry but we couldn\'t send your message, try again in a moment.');
                })
                .always(function()
                {
                    $('.loading').hide();
                    $this.removeClass('nosubmit');
                });
            })
            .fail(function(jqXHR, textStatus, errorThrown)
            {
                $('#contact-us-feedback').prop('class', 'contact-us-failure');
                $('#contact-us-feedback')[0].innerHTML = gettext('Sorry but we couldn\'t send your message, try again in a moment.');
                $('.loading').hide();
                $this.removeClass('nosubmit');
            });
        });
    }

    if($('form#form-save-merchant-shipment')[0])
    {
        $('button#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
        });

        $('form#form-save-merchant-shipment').validate(
        {
            ignore: '#id_product_set-__prefix__-quantity',
            submitHandler: function(form)
            {
                $('.loading').show();
                sessionStorage.removeItem('shipment_products');
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('button#send-btn').removeClass('nosubmit');
                $('<label id="send-btn-error" class="error" for="send-btn">' + gettext('Fix the errors above and try again.') + '</label>').insertAfter('button#send-btn');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });

        window.addRule = function(element, rules)
        {
            element.rules('add', rules);
        }

        $('.quantity_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        });
        $('.type_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
        $('.products_validate').each(function ()
        {
            $(this).rules('add',
            {
                productsNotEmpty: true,
            });
        });
    }

    $('.add-service-product-shipment').click(function()
    {
        var pid = $(this).data('shipment-product-id');
        var puid = $(this).data('shipment-product-uid');
        var addServiceProduct = $('#add-service-product');
        var form = addServiceProduct.closest('form');
        form.find('input[name="service_product_id"]').val(pid);
        form.find('input[name="shipment_product_uid"]').val(puid);
        $('.loading').show();
        $.ajax(
        {
            method: 'GET',
            url: '/' + gettext('en') + '/service/product/' + pid + '/?puid=' + puid
        }).done(function( obj )
        {
            if(form[0])
                form[0].reset();
            addServiceProduct.find('span').each(function ()
            {
                $(this).hide();
            });
            obj.products.forEach(function(item)
            {
                addServiceProduct.find('input[name="service"]').each(function ()
                {
                    if(''+item.service_id === this.value)
                    {
                        this.checked=true;
                        addServiceProduct.find('input[name="price' + this.value + '"]').val(item.service_price);
                        return false;
                    }
                });
                addServiceProduct.find('span[id="service_'+item.service_id+'"]').each(function ()
                {
                    $(this).show();
//                        addServiceProduct.find('input[name="price' + this.value + '"]').val(item.service_price);
                });
            });
            $('.loading').hide();
            addServiceProduct.modal('show');
        });
    });

    $('#send-btn-add-service-product').click(function()
    {
        var addServiceProduct = $('#add-service-product');
        var form = addServiceProduct.closest('form');
        $('.loading').show();
        $.ajax(
        {
            method: 'POST',
            url: '/' + gettext('en') + '/service/product/' + form.find('input[name="service_product_id"]').val() + '/',
            data: form.serialize()
        }).done(function( obj )
        {
            var totalCost = $('#totalCost');
            if(totalCost[0])
            {
                var pElement = totalCost.closest('p');
                if(obj.new_cost_raw > 0)
                {
                    pElement.removeAttr('class');
                    $('.minimum-value-alert').removeClass('hide');
                }
                else
                {
                    pElement.attr('class', 'hide');
                    $('.minimum-value-alert').addClass('hide');
                }
                totalCost[0].innerHTML = obj.new_cost;
            }
            var productServiceValidation = $('#services' + form.find('input[name="service_product_id"]').val());
            if(productServiceValidation[0])
            {
                if(obj.v > 0)
                    productServiceValidation.val('1');
                else
                    productServiceValidation.val('');
            }
        })
        .always(function()
        {
            form[0].reset();
            $('.loading').hide();
            addServiceProduct.modal('hide');
        });
    });

    var deleteShipmentService = function()
    {
//TODO implementar
    };

    $('.delete-shipment-service').click(deleteShipmentService);

    $('#btn-add-service-shipment').click(function()
    {
        var sid = $(this).data('shipment-id');
        var addServiceShipment = $('#add-service-shipment');
        var form = addServiceShipment.closest('form');
        form.find('input[name="service_shipment_id"]').val(sid);
        $('.loading').show();
        $.ajax(
        {
            method: 'GET',
            url: '/' + gettext('en') + '/service/shipment/' + sid + '/'
        }).done(function( obj )
        {
            if(form[0])
                form[0].reset();
            addServiceShipment.find('span').each(function ()
            {
                $(this).hide();
            });
            obj.shipment_services.forEach(function(item)
            {
                addServiceShipment.find('input[name="service"]').each(function ()
                {
                    if(''+item.service_id === this.value)
                    {
                        this.checked=true;
                        addServiceShipment.find('input[name="price' + this.value + '"]').val(item.service_price);
                        addServiceShipment.find('input[name="quantity' + this.value + '"]').val(item.service_quantity);
                        return false;
                    }
                });
                addServiceShipment.find('span[id="service_shipment_'+item.service_id+'"]').each(function ()
                {
                    $(this).show();
                });
            });
            $('.loading').hide();
            addServiceShipment.modal('show');
        });
    });

    $('#send-btn-add-service-shipment').click(function()
    {
        var addServiceShipment = $('#add-service-shipment');
        var form = addServiceShipment.closest('form');
        $('.loading').show();
        $.ajax(
        {
            method: 'POST',
            url: '/' + gettext('en') + '/service/shipment/' + form.find('input[name="service_shipment_id"]').val() + '/',
            data: form.serialize()
        }).done(function( obj )
        {
            var totalCost = $('#totalCost');
            if(totalCost[0])
            {
                var pElement = totalCost.closest('p');
                if(obj.new_cost_raw > 0)
                {
                    pElement.removeAttr('class');
                    $('.minimum-value-alert').removeClass('hide');
                }
                else
                {
                    pElement.attr('class', 'hide');
                    $('.minimum-value-alert').addClass('hide');
                }
                totalCost[0].innerHTML = obj.new_cost;
            }
            var row = 1;
            $('#table-shipment-services tbody').find("tr:gt(0)").remove();
            obj.shipment_services.forEach(function(item)
            {
                var newRow = $('#row-shipment-services-template')
                  .clone()
                  .attr('id', 'row' + (row++))
                  .appendTo($('#table-shipment-services tbody'));
                newRow.find('td').each(function(index)
                {
                    switch(index)
                    {
                        case 0:
                            $(this).append(item.service_name);
                            break;
                        case 1:
                            $(this).append(item.service_quantity);
                            break;
                        case 2:
                            $(this).append(item.service_price);
                            break;
                        case 3:
                            var anchor = $(this).find('a');
                            anchor.attr('title', gettext('Excluir') + ' ' + item.service_name);
                            anchor.attr('data-delete-shipment-service-id', item.service_id);
                            anchor.click(deleteShipmentService);
                            break;
                    }
                });
                newRow.show();
            });
        })
        .always(function()
        {
            form[0].reset();
            $('.loading').hide();
            addServiceShipment.modal('hide');
        });
    });

    var fcountdown = function(_this, countDownDate)
    {
          // Get todays date and time
          var now = new Date(new Date().toUTCString().substring(0, 25))

          // Find the distance between now an the count down date
          var distance = countDownDate - now;

          var hours = 0;
          var minutes = 0;
          var seconds = 0;
          if(distance > 0)
          {
              // Time calculations for days, hours, minutes and seconds
              hours = Math.floor(distance / (1000 * 60 * 60));
              minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
              seconds = Math.floor((distance % (1000 * 60)) / 1000);
          }

          // Display the result in the element with id="demo"
          _this.innerHTML = "<i class='far fa-clock'></i> " + hours + "h "
          + minutes + "m " + seconds + "s ";

          return distance;
    };

    $('p.countdown').each(function ()
    {
        // Set the date we're counting down to
        var countDownDate = new Date($(this).data('countdown')).getTime();
        var _this = this;

        // Update the count down every 1 second
        var x = setInterval(function()
        {
          var distance = fcountdown(_this, countDownDate);

          // If the count down is finished, write some text
          if (distance < 0)
          {
            clearInterval(x);
            _this.innerHTML = gettext('EXPIRED');
          }
        }, 1000);
    });

    $('.add-pro').click(function()
    {
        var numeroProduto = Number($('.lista-produtos .produto:last-child .num-produto').text()) + 1;

        $('.lista-produtos').append("<div class='produto'>" +
                "<label class='titulo'>Protuto <span class='num-produto'>" + numeroProduto + "</span></label>" +
                 "<div class='form-group col-md-12'>" +
                        "<label for='nome-produto-" + numeroProduto + "'>Nome Produto</label>" +
                        "<input type='text' class='form-control' id='nome-produto-" + numeroProduto + "' placeholder='Digite nome do Produto...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='UPC-" + numeroProduto + "'>UPC / Codigo identificador</label>" +
                   "    <input type='text' class='form-control' id='UPC-" + numeroProduto + "' placeholder='Digite UPC...'>" +
                  "</div><br> " +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='valor-compra-" + numeroProduto + "'>Valor compra</label>" +
                    "    <input type='text' class='form-control' id='valor-compra-" + numeroProduto + "' placeholder='Digite Valor compra...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='Quantidade-" + numeroProduto + "'>Quantidade</label>" +
                    "    <input type='text' class='form-control' id='Quantidade-" + numeroProduto + "' placeholder='Digite Quantidade...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='total-produto-" + numeroProduto + "'>Total a pagar do produto</label>" +
                    "    <input type='text' class='form-control' id='total-produto-" + numeroProduto + "' placeholder='Digite Total a pagar...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='valor-venda-" + numeroProduto + "'>Valor venda</label>" +
                    "    <input type='text' class='form-control' id='valor-venda-" + numeroProduto + "' placeholder='Digite valor venda...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'> " +
                   "     <label for='fba-" + numeroProduto + "'>FBA fee</label>" +
                    "    <input type='text' class='form-control' id='fba-" + numeroProduto + "' placeholder='Digite FBA fee...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='Amazon-" + numeroProduto + "'>Amazon fee</label>" +
                    "    <input type='text' class='form-control' id='Amazon-" + numeroProduto + "' placeholder='Digite Amazon fee...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='envio-" + numeroProduto + "'>Envio para Amazon</label>" +
                    "    <input type='text' class='form-control' id='envio-" + numeroProduto + "' placeholder='Digite Envio...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='Redirecionamento-" + numeroProduto + "'>Redirecionamento</label>" +
                    "    <input type='text' class='form-control' id='Redirecionamento-" + numeroProduto + "' placeholder='Digite Redirecionamento...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='lucro-unidade-" + numeroProduto + "'>Lucro liquido por unidade</label>" +
                    "    <input type='text' class='form-control' id='lucro-unidade-" + numeroProduto + "' placeholder='Digite lucro por unidade...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='lucro-total-" + numeroProduto + "'>Lucro total</label>" +
                    "    <input type='text' class='form-control' id='lucro-total-" + numeroProduto + "' placeholder='Digite Lucro total...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'> " +
                   "     <label for='roi-produto-" + numeroProduto + "'>ROI (%)</label>" +
                    "    <input type='text' class='form-control' id='roi-produto-" + numeroProduto + "' placeholder='Digite ROI...'>" +
                  "</div>" +
                  "<a class='rem-track btn btn-danger' data-toggle='tooltip' title='Remover produto' href='#'><i class='fa fa-fw fa-times'></i> Remover este produto do lote</a>" +
                "</div>");
    });

    //Tabs pagina ajuda
    $("#ajudatab li:eq(0) a").tab('show');

    //Modal tutorial
    $('#abre-codigo').click(function(){
        $('#modal-codigo').modal('show');
    });

    $('#link-unsubscribe-VP').click(function(){
        $('#modal-unsubscribe-VP').modal('show');
    });

    $('#link-unsubscribe-WC').click(function(){
        $('#modal-unsubscribe-WC').modal('show');
    });

    $("#abre-endereco").click(function(){
        $('#modal-endereco').modal('show');
    });

    //Modal tutorial
    $('.abre-tutorial').click(function(){
        $('#tutorial').modal('show');
    });

    //Modal verificar cubagem
    $('#ver-espaco').click(function(){
        $('#espaco').modal('show');
    });


    //Modal tutorial redirecionamento BR
    $('#video-explicativo-br').click(function(){
        $('#tutorial-br').modal('show');
    });

    //popup servicos de prep
    $('.inline-service').click(function(){
        $(this).parent("td").find(".modal").modal('show');
    });

    //Click radio cadastro de envio brasil
    $(".endereco-cadastro-chk").click(function(){
         var classe = $(this).find("input[type='radio']").attr("class");
         if(classe == "endereco-novo"){
            $(".endereco-novo-form").show();
         }else{
            $(".endereco-novo-form").hide();
         }
    });

    //Edicao de arquivos das etiquetas
    $(".edit-pdf").click(function(){
        $(this).parent().hide();
        $(this).parent().parent().find(".input-content-edit-pdf").show();
    });

    $(".edit-pdf-undo").click(function(){
        $(this).parent().find('input:file').val('')
        $(this).parent().hide();
        $(this).parent().parent().find(".link-download-pdf").show();
    });

        $('form#form-add-colab').validate(
        {
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
//            invalidHandler: function(event, validator)
//            {
//                $('button#send-btn').removeClass('nosubmit');
//                $('.send-btn-error').remove();
//                $('<label class="error send-btn-error" for="send-btn">' + gettext('Fix the errors above and try again.') + '</label>').insertAfter('button#send-btn');
//            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });

        $('input#collab_name').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });

        $('input#collab_email').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                email: true,
            });
        });

        $('input#collab_phone').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        });

        $('textarea#collab_message').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });

        //change select FBM FBA

        $( ".select-fbs" ).change(function() {

            $(".boxes-fb").removeClass("active");
            var tipo = "";

            $( "select option:selected" ).each(function() {

              tipo += $( this ).text() + " ";
              $("#" + tipo).adClass("active");

            });
        });

        //controle quantidade string título mobile

        if((window.screen.width >= 280) && (window.screen.width <= 768)){

            $('.parceiro h6').html($('.parceiro h6').text().substring(0,38) + '...');

        }

})(jQuery); // End of use strict
