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

    // Closes the Responsive Menu on Menu Item Click
    $('.navbar-collapse ul li a').click(function()
    {
            $('.navbar-toggle:visible').click();
    });

    if($('body.index #mainNav').affix)
    {
        // Offset for Main Navigation
        $('body.index #mainNav').affix(
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

        $.datepicker.setDefaults($.datepicker.regional['pt-BR']);

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
                dateLessThanOrEqualNow: gettext('Please enter a date less than or equal today.'),
                positiveNumber: gettext('Please enter a number greater than zero.'),
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
                address_1: { required: true },
                neighborhood: { required: true },
                city: { required: true },
                state: { required: true },
                zipcode: { required: true },
                password:
                {
                    required: true,
//                    minlength: 6,
//                    passwordFormat: true
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
            $('form#form-login').attr('action', '/login/');
        });

        $('a#forgot-password-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
            $('form#form-login').attr('action', '/user/password/forgot/');
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
                          return $('form#form-login').attr('action') === '/login';
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
                    minlength: 6,
                    passwordFormat: true
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
        $('.send_date_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                date: true,
                dateLessThanOrEqualNow: true,
            });
        });
    }

    $('.send-btn-async').click(function()
    {
        var form = $(this).closest('form.form-change-status');
        var pid = form.find('input.product-id').val();
        if(form.attr('id').split('-')[3] === pid)
        {
            var radioChecked = form.find('input:radio:checked');
            if(radioChecked[0])
            {
                var checkedValue = radioChecked.val();
                var currentValue = radioChecked.attr('data-current-status');
                if(checkedValue !== currentValue)
                {
                    $.ajax(
                    {
                        method: 'PUT',
                        url: '/product/edit/status/' + pid + '.json',
                        data: form.serialize()
                    })
                    .done(function( obj )
                    {
                        $('span#product-status-display-'+obj.product.id).text(obj.product.status_display);
                        form.find('input:radio').attr('data-current-status', obj.product.status);
                        if(obj.product.show_check && obj.product.status === SHIPMENT_STATUS_IN_STOCK && obj.product.quantity >= 0)
                        {
                            var checkbox = $('<input type="checkbox" name="shipment_product" value="' + obj.product.id + '" id="shipment-' + obj.product.id + '" class="shipment-product" />');
                            $('span#product-status-display-'+obj.product.id).closest('td').next().append(checkbox);
                        }
                        else
                        {
                            $('span#product-status-display-'+obj.product.id).closest('td').next()[0].innerHTML = '';
                        }
                        form.closest('.contem-status').hide();
                    });
                }
            }
        }
        return false;
    });

    $('.send-btn-delete').click(function()
    {
        $('#confirmacao-exclusao').modal('show');
    });

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
        var shipmentForm = $('#form-add-shipment');
        $('#btn-add-shipment').click(function()
        {
            var get = true;
            $('.shipment-product:checked').each(function()
            {
                var checkedProduct = $('<input type="hidden" name="shipment_product"></input>');
                checkedProduct.val($(this).val());
                checkedProduct.appendTo(shipmentForm);
                get = false;
            });
            if(get)
            {
                window.location.href = shipmentForm.attr('action');
            }
            else
            {
                shipmentForm.submit();
            }
        });
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

        window.addRule = function(element)
        {
            element.rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        }

        $('.quantity_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                positiveNumber: true,
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
        $('.pdf_1-validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
    }

    if($('form.form-filter')[0] && $('ul.pagination')[0])
    {
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
            $('form.form-filter').submit();
        });
    }

    if($('form#form-add-package')[0])
    {
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
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('a#send-btn-1').removeClass('nosubmit');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });

        window.addRule = function(element)
        {
            element.rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        }

        $('input.add-validate-rule').each(function ()
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
            var form = $(this).closest('form');
            $.ajax(
            {
                method: 'DELETE',
                url: '/shipment/delete/product',
                data: form.serialize(),
                statusCode:
                {
                    400: function()
                    {
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
                tr.remove();
                $('#totalProducts')[0].innerHTML = obj.items;
                $('#totalCost')[0].innerHTML = obj.cost;
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
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });

        $('.pdf_2-validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
    }

    if($('form#form-add-shipment')[0])
    {
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
                $('form#form-add-shipment').submit();
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
                $('form#form-add-shipment').submit();
            });
        }
    }

    function assembleModal(title, body)
    {
        $('div.modal-content h4.modal-title')[0].innerHTML = title;
        var modalBody = $('div.modal-content div.modal-body');
        modalBody[0].innerHTML = '';
        modalBody.append($('<p>' + body + '</p>'));
        $('#confirmacao').modal('show');
    }

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

    //Modal tutorial
    $('.abre-tutorial').click(function(){
        $('#tutorial').modal('show');
    });

})(jQuery); // End of use strict
