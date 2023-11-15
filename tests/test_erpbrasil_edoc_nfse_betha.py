# Copyright (C) 2023  Antônio Salvador Pereira Neto - Engenere

import os
from unittest import TestCase
from requests import Session

from erpbrasil.assinatura.certificado import Certificado
from erpbrasil.transmissao import TransmissaoSOAP

from erpbrasil.edoc.provedores.cidades import NFSeFactory

from nfselib.bindings.betha.servico_enviar_lote_rps_envio_v01 import EnviarLoteRpsEnvio
from nfselib.bindings.betha.tipos_nfe_v01 import (
    TcCpfCnpj,
    TcDadosServico,
    TcDadosTomador,
    TcEndereco,
    TcIdentificacaoPrestador,
    TcIdentificacaoRps,
    TcIdentificacaoTomador,
    TcInfRps,
    TcLoteRps,
    TcRps,
    TcValores,
)


class BethaTests(TestCase):
    """Testa a comunicação com o provedor de NFS-e Betha"""

    def setUp(self):
        # Para usar um certificado válido configure
        # as variaveis de ambiente `PFX_PATH` e `PFX_PASSWORD`
        certificado_nfe_caminho = os.environ.get(
            'PFX_PATH',
            'test/fixtures/dummy_cert.pfx'
        )
        certificado_nfe_senha = os.environ.get(
            'PFX_PASSWORD', 'dummy_password'
        )

        self.certificado = Certificado(
            certificado_nfe_caminho,
            certificado_nfe_senha
        )

        session = Session()
        session.verify = False

        transmissao = TransmissaoSOAP(self.certificado, session)
        self.nfse_client = NFSeFactory(
            transmissao=transmissao,
            ambiente="2",  # 2 = Homologação, 1 = Produção
            cidade_ibge=4216305,
            cnpj_prestador="48460292000171",
            im_prestador="8365",
        )

        self.lote_rps = self.create_lote_rps()
        self.inf_nfse = None

    def test_enviar_nfse(self):
        "Testa a transmissão da NFS-e"
        for processo in self.nfse_client.processar_documento(self.lote_rps):
            if processo.webservice in "ConsultarLoteRpsEnvio":
                self.inf_nfse = processo.resposta.lista_nfse.compl_nfse[0].nfse.inf_nfse
        self.assertTrue(self.inf_nfse)

    def test_consultar_nfse(self):
        "Testa a consulta da NFS-e"
        ident_rps = self.lote_rps.LoteRps.ListaRps.Rps[0].InfRps.IdentificacaoRps
        processo = self.nfse_client.consulta_nfse_rps(
            rps_number=ident_rps.Numero,
            rps_serie=ident_rps.Serie,
            rps_type=ident_rps.Tipo,
        )
        nfse = processo.resposta.compl_nfse
        self.assertTrue(nfse)

    def test_cancelar_nfse(self):
        "Testa o cancelamento da NFS-e"
        numero = self.inf_nfse.numero
        processo = self.nfse_client.cancela_documento(numero)
        self.assertTrue(processo.resposta.cancelamento)

    def create_lote_rps(self):
        return EnviarLoteRpsEnvio(
            LoteRps=TcLoteRps(
                Cnpj='48460292000171',
                InscricaoMunicipal="8365",
                QuantidadeRps=1,
                ListaRps=TcLoteRps.ListaRps(
                    Rps=[
                        TcRps(
                            InfRps=TcInfRps(
                                Id='rps343',
                                IdentificacaoRps=TcIdentificacaoRps(
                                    Numero=343,
                                    Serie=111,
                                    Tipo=1,
                                ),
                                DataEmissao='2020-11-20T12:00:21',
                                NaturezaOperacao=1,
                                RegimeEspecialTributacao=1,
                                OptanteSimplesNacional=2,
                                IncentivadorCultural=2,
                                Status=1,
                                RpsSubstituido=None,
                                Servico=TcDadosServico(
                                    Valores=TcValores(
                                        ValorServicos=100.0,
                                        ValorDeducoes=0.0,
                                        ValorPis=0.0,
                                        ValorCofins=0.0,
                                        ValorInss=0.0,
                                        ValorIr=0.0,
                                        ValorCsll=0.0,
                                        IssRetido=2,
                                        ValorIss=3.0,
                                        ValorIssRetido=0.0,
                                        OutrasRetencoes=0.0,
                                        BaseCalculo=100.0,
                                        Aliquota=3.00,
                                        ValorLiquidoNfse=100.0,
                                    ),
                                    ItemListaServico='0101',
                                    CodigoCnae=6202300,
                                    Discriminacao='[ODOO_DEV] Código de Ativação Técnico',  # importante testar com os acentos
                                    CodigoMunicipio=4216305,
                                ),
                                Prestador=TcIdentificacaoPrestador(
                                    Cnpj='48460292000171',
                                    InscricaoMunicipal='8365',
                                ),
                                Tomador=TcDadosTomador(
                                    IdentificacaoTomador=TcIdentificacaoTomador(
                                        CpfCnpj=TcCpfCnpj(
                                            Cnpj='48460292000171',
                                            Cpf=None,
                                        ),
                                        InscricaoMunicipal=None,
                                    ),
                                    RazaoSocial="Empresa do Fulano",
                                    Endereco=TcEndereco(
                                        Endereco='Rua do Marcolino',
                                        Numero='123',
                                        Complemento=None,
                                        Bairro='Centro',
                                        CodigoMunicipio=3550308,
                                        Uf='SC',
                                        Cep=4576060,
                                    ) or None,
                                ),
                                IntermediarioServico=None,
                                ConstrucaoCivil=None,
                            )
                        )
                    ]
                )
            )
        )
