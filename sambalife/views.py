# -*- coding: utf-8 -*-

from django.shortcuts import render

def login(request):
    return render(request, 'login.html')

def usuarios(request):
    return render(request, 'lista_usuarios.html')

def usuarioDetalhe(request):
    return render(request, 'usuario_detalhe.html')

def usuarioCadastro(request):
    return render(request, 'usuario_cadastro.html')

def pagamentos(request):
    return render(request, 'lista_pagamentos.html')

def pagamentoDetalhe(request):
    return render(request, 'pagamento_detalhe.html')

def estoque(request):
    return render(request, 'estoque.html')

def detalheProduto(request):
    return render(request, 'produto_detalhe.html')

def cadastroProduto(request):
    return render(request, 'produto_cadastro.html')

def shipments(request):
    return render(request, 'lista_shipment.html')

def detalheShipment(request):
    return render(request, 'shipment_detalhe.html')

def cadastroShipment(request):
    return render(request, 'shipment_cadastro.html')

