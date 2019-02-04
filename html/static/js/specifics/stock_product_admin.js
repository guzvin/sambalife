(function($)
{
    'use strict';
    $(function()
    {
        $('#id_identifier-fill_out').click(function()
        {
            if($.trim($('input#id_identifier').val()) && $.trim($('select#id_condition').val()))
            {
                $.ajax(
                {
                    method: 'POST',
                    crossDomain: true,
                    url: 'https://app.voiservices.com:3031/api/getproduct',
                    data: {asin: $.trim($('input#id_identifier').val()),
                            condicao: $.trim($('select#id_condition option:selected').text())},
                })
                .done(function(response_data)
                {
                    if($.trim(response_data.Nome))
                    {
                        $('input#id_name').val(response_data.Nome);
                        $('input#id_upc').val(response_data.UPC);
                        $('input#id_url').val(response_data.URL);
                        $('input#id_buy_price').val(response_data.Preco_Cliente);
                        $('input#id_sell_price').val(response_data.BuyBox);
                        $('input#id_rank').val(response_data.Rank);
                        $('input#id_fba_fee').val(response_data.Fee);
                        $('input#id_shipping_cost').val(response_data.Shipping);
                    }
                    else
                    {
                        $('input#id_name').val('');
                        $('input#id_upc').val('');
                        $('input#id_url').val('');
                        $('input#id_buy_price').val('');
                        $('input#id_sell_price').val('');
                        $('input#id_rank').val('');
                        $('input#id_fba_fee').val('');
                        $('input#id_shipping_cost').val('');
                    }
                });
            }
        });

        $('#id_upc-fill_out').click(function()
        {
            if($.trim($('input#id_upc').val()) && $.trim($('select#id_condition').val()))
            {
                $.ajax(
                {
                    method: 'POST',
                    crossDomain: true,
                    url: 'https://app.voiservices.com:3031/api/getproduct',
                    data: {upc: $.trim($('input#id_upc').val()),
                            condicao: $.trim($('select#id_condition option:selected').text())},
                })
                .done(function(response_data)
                {
                    if($.trim(response_data.Nome))
                    {
                        $('input#id_name').val(response_data.Nome);
                        $('input#id_identifier').val(response_data.ASIN);
                        $('input#id_url').val(response_data.URL);
                        $('input#id_buy_price').val(response_data.Preco_Cliente);
                        $('input#id_sell_price').val(response_data.BuyBox);
                        $('input#id_rank').val(response_data.Rank);
                        $('input#id_fba_fee').val(response_data.Fee);
                        $('input#id_shipping_cost').val(response_data.Shipping);
                    }
                    else
                    {
                        $('input#id_name').val('');
                        $('input#id_identifier').val('');
                        $('input#id_url').val('');
                        $('input#id_buy_price').val('');
                        $('input#id_sell_price').val('');
                        $('input#id_rank').val('');
                        $('input#id_fba_fee').val('');
                        $('input#id_shipping_cost').val('');
                    }
                });
            }
        });
    });
})(django.jQuery); // End of use strict