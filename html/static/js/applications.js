// Agency Theme JavaScript

(function($) {
    'use strict'; // Start of use strict

    // jQuery for page scrolling feature - requires jQuery Easing plugin
    $('a.page-scroll').bind('click', function(event) {
        var $anchor = $(this);
        $('html, body').stop().animate({
            scrollTop: ($($anchor.attr('href')).offset().top - 50)
        }, 1250, 'easeInOutExpo');
        event.preventDefault();
    });

    // Highlight the top nav as scrolling occurs
    $('body.index').scrollspy({
        target: '.navbar-fixed-top',
        offset: 51
    });

    // Closes the Responsive Menu on Menu Item Click
    $('.navbar-collapse ul li a').click(function(){ 
            $('.navbar-toggle:visible').click();
    });

    // Offset for Main Navigation
    $('body.index #mainNav').affix({
        offset: {
            top: 100
        }
    })
    
    $('.mudar-status').click(function(){
        $(this).parent('td').find('.contem-status').show();                               
    });
    
    $('.fechar').click(function(){
        $(this).parent('.status').parent('.contem-status').hide();                               
    });
    
    $('.alterar-status').click(function(){
		$('#confirmacao').modal('show');
	});
    
    $.datepicker.regional['pt-BR'] = {
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
    
    $( "#datepicker" ).datepicker();
    
    $("[data-toggle='tooltip']").tooltip({
        placement : 'top'
    });

    $('.add-pro').click(function(){
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

    $('.add-track').click(function(){

        var numeroTrack = Number($('.lista-tracks .group-track:last-child .num-track').text()) + 1;
        console.log(numeroTrack);
        $('.lista-tracks').append("<div class='form-group group-track'>" +
                    "<div class='col-md-5'>" +
                      "  <label for='Track-" + numeroTrack + "'>Track Number <span class='num-track'>" + numeroTrack + "</span></label>" +
                     "   <input type='number' class='form-control' id='Track-" + numeroTrack + "' placeholder='Digite o Track Number...' />" +
                    "</div>" +
                    "<div class='col-md-7 content-btn-add'>" +
                    "    <a class='rem-track btn btn-danger' data-toggle='tooltip' title='Remover este Track number' href='#'><i class='fa fa-fw fa-times'></i></a>" +
                   " </div><br>" +
                  "</div>");
    });

})(jQuery); // End of use strict
