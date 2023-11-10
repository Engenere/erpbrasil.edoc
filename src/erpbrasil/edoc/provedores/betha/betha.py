# Copyright (C) 2023  Antônio Salvador Pereira Neto - Engenere

from lxml import etree

from erpbrasil.assinatura.assinatura import XMLSignerWithSHA1

from erpbrasil.edoc.nfse import NFSe
from erpbrasil.edoc.nfse import ServicoNFSe
from erpbrasil.edoc.resposta import RetornoSoap
import signxml
from urllib.parse import urljoin

from xsdata.formats.dataclass.transports import DefaultTransport
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.formats.dataclass.client import Client

from .generated import nfse_v202
from .generated_wsdl import consultar_lote_rps, recepcionar_lote_rps, cancelar_nfse
from .generated_wsdl.consultar_nfse_por_rps import (
    ConsultarNeporRpsConsultarNfsePorRpsEnvio,
    ConsultarNeporRpsConsultarNfsePorRpsEnvioInput,
    ConsultarNeporRpsConsultarNfsePorRpsEnvioOutput,
    ConsultarNfsePorRpsEnvio,
    TcPedidoCancelamento,
    TcInfPedidoCancelamento,
    TcIdentificacaoNfse,
    TcIdentificacaoRps,
    TcIdentificacaoPrestador
)

# Definição dos serviços (WSDL)
HOMO_BASE_URL = "https://e-gov.betha.com.br/e-nota-contribuinte-test-ws/"
PROD_BASE_URL = "https://e-gov.betha.com.br/e-nota-contribuinte-ws/"
servicos = {
    'envia_documento': ServicoNFSe(
        operacao='EnviarLoteRpsEnvio',
        endpoint='recepcionarLoteRps',
        classe_retorno=nfse_v202,
        assinar=True
    ),
    'consultar_lote_rps': ServicoNFSe(
        operacao='ConsultarLoteRpsEnvio',
        endpoint='consultarLoteRps',
        classe_retorno=nfse_v202,
        assinar=True),
    'cancela_documento': ServicoNFSe(
        operacao='CancelarNfseEnvio',
        endpoint='cancelarNfse?wsdl',
        classe_retorno=nfse_v202,
        assinar=True),
    'consulta_nfse_rps': ServicoNFSe(
        operacao='ConsultarNfsePorRpsEnvio',
        endpoint='consultarNfsePorRps',
        classe_retorno=nfse_v202,
        assinar=True),
}


class Betha(NFSe):
    """
    Classe responsável por realizar a transmissão de notas fiscais
    através do webservice do provedor Betha.
    """
    _header = None

    def __init__(self, transmissao, ambiente, cidade_ibge, cnpj_prestador,
                 im_prestador):
        if ambiente == '2':
            self._url = HOMO_BASE_URL
        else:
            self._url = PROD_BASE_URL
        self._servicos = servicos

        super().__init__(
            transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador)

    def get_documento_id(self, edoc):
        return edoc.LoteRps.Id, edoc.LoteRps.NumeroLote

    # OVERRIDE
    def envia_documento(self, edoc):
        servico = self._servicos[self.envia_documento.__name__]
        numero_lote = self._gera_numero_lote()
        edoc.LoteRps.Id = 'lote' + numero_lote
        edoc.LoteRps.NumeroLote = int(numero_lote)

        # aqui é redenrizado para string e depois serializado para o objeto novamente.
        # mas desta vez o tipo do objeto corresponde com o que foi gerado a partir do WSDL.
        xml_string, xml_etree = self._render_edoc(edoc)
        enviar_lote_rps_envio = XmlParser().from_string(
            source=xml_string,
            clazz=recepcionar_lote_rps.EnviarLoteRpsEnvio
        )

        for rps in edoc.LoteRps.ListaRps.Rps:
            rps_signed_root = self.sign(rps, rps.InfRps.Id)
        enviar_lote_soap = recepcionar_lote_rps.RecepcionarLoteRpsEnviarLoteRpsEnvioInput(
            body=recepcionar_lote_rps.RecepcionarLoteRpsEnviarLoteRpsEnvioInput.Body(
                enviar_lote_rps_envio=enviar_lote_rps_envio
            )
        )
        # recupera a requisição SOAP no formato lxml tree.
        enviar_lote_soap_root = etree.fromstring(
            XmlSerializer().render(
                enviar_lote_soap,
            ).encode("utf-8")
        )
        # Selecionar a tag desejada com atributo Id="rps1"
        rps_tag = enviar_lote_soap_root.xpath('//Rps')[0]
        # Modificar o conteúdo da tag se ela for encontrada
        if rps_tag is not None:
            rps_tag.clear()
            rps_tag.extend(rps_signed_root)
        payload = etree.tostring(
            enviar_lote_soap_root, encoding='utf-8'
        ).decode('utf-8')

        transport = DefaultTransport(session=self._transmissao.session)
        enviar_lote_response = transport.post(
            data=payload,
            url=self._get_location(servico),
            headers=None
        )
        retorno = XmlParser().from_bytes(
            source=enviar_lote_response,
            clazz=recepcionar_lote_rps.RecepcionarLoteRpsEnviarLoteRpsEnvioOutput
        )

        # Extrai apenas a parte relevante do envelope SOAP.
        if retorno.body.enviar_lote_rps_envio_response:
            resposta = retorno.body.enviar_lote_rps_envio_response.enviar_lote_rps_resposta

        return RetornoSoap(
            webservice=servico.operacao,
            raiz=xml_etree,
            xml=xml_string,
            retorno=retorno,
            resposta=resposta
        )

    def consulta_recibo(self, proc_envio):
        """
        Consulta o lote de RPS utilizando a comunicação SOAP do XSDATA.
        """
        servico = self._servicos[self.consultar_lote_rps.__name__]

        protocolo = proc_envio.resposta.protocolo
        consultar_lote_rps_envio = self._prepara_consultar_lote_rps(protocolo)

        xml_body = XmlSerializer().render(consultar_lote_rps_envio)
        client = Client.from_service(
            consultar_lote_rps.ConsultarLoteRpsConsultarLoteRpsEnvio,
            location=self._get_location(servico)
        )

        session = self._transmissao.session
        transport = DefaultTransport(session=session)
        client.transport = transport
        consultar_input = consultar_lote_rps.ConsultarLoteRpsConsultarLoteRpsEnvioInput
        request_recibo = consultar_input(
            body=consultar_input.Body(
                consultar_lote_rps_envio=consultar_lote_rps_envio
            )
        )
        retorno: consultar_lote_rps.ConsultarLoteRpsConsultarLoteRpsEnvioOutput
        retorno = client.send(request_recibo)
        # TODO Verificar se houve falhas (fault) no retorno.

        # Extrai apenas a parte relevante do envelope SOAP.
        resposta = retorno.body.consultar_lote_rps_envio_response.consultar_lote_rps_resposta

        # O retorno aqui é o XML que representa de fato a NFS-e emitida,
        xml_nfse = None
        if resposta.lista_nfse.compl_nfse:
            xml_nfse = XmlSerializer().render(resposta.lista_nfse.compl_nfse[0])

        return RetornoSoap(
            webservice=servico.operacao,
            raiz=xml_body,
            xml=xml_body,
            retorno=xml_nfse,
            resposta=resposta
        )

    def cancela_documento(self, doc_numero):
        """
        Cancelamento da NFS-e utilizando a comunicação SOAP do XSDATA.
        """
        servico = self._servicos[self.cancela_documento.__name__]
        client = Client.from_service(
            cancelar_nfse.CancelarNev01CancelarNfseEnvio,
            location=self._get_location(servico)
        )
        session = self._transmissao.session
        transport = DefaultTransport(session=session)
        client.transport = transport
        cancelar_nfse_envio = self._prepara_cancelar_nfse_envio(doc_numero)
        cancelar_input_obj = cancelar_nfse.CancelarNev01CancelarNfseEnvioInput
        cancelar_input = cancelar_input_obj(
            body=cancelar_input_obj.Body(cancelar_nfse_envio)
        )
        cancelar_output: cancelar_nfse.CancelarNev01CancelarNfseEnvioOutput
        cancelar_output = client.send(cancelar_input)

        # Extrai apenas a parte relevante do envelope SOAP.
        cancelar_nfse_reposta = (
            cancelar_output.body.cancelar_nfse_envio_response
            .cancelar_nfse_reposta
        )

        config = SerializerConfig(pretty_print=True)
        serializer = XmlSerializer(config=config)

        xml_input = serializer.render(cancelar_nfse_envio)
        xml_output = serializer.render(cancelar_nfse_reposta)

        return RetornoSoap(
            webservice=servico.operacao,
            raiz=cancelar_nfse_envio,
            xml=xml_input,
            retorno=xml_output,
            resposta=cancelar_nfse_reposta
        )

    def _prepara_consultar_lote_rps(self, protocolo):
        raiz = consultar_lote_rps.ConsultarLoteRpsEnvio(
            prestador=consultar_lote_rps.TcIdentificacaoPrestador(
                cnpj=self.cnpj_prestador,
                inscricao_municipal=self.im_prestador
            ),
            protocolo=protocolo
        )
        return raiz

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        if proc_envio.resposta.protocolo:
            return True
        return False

    def _edoc_situacao_em_processamento(self, proc_recibo):
        """
        Verifica se a situação do lote de RPS associado ao recibo de processamento
        está atualmente em processamento.
        """
        response: consultar_lote_rps.ConsultarNotaResp
        response = proc_recibo.resposta
        mensagem_retorno = response.lista_mensagem_retorno.mensagem_retorno
        code = mensagem_retorno[0].codigo if mensagem_retorno else False
        # E92: RPS ainda não processado
        if code == 'E92':
            return True
        return False

    def _prepara_cancelar_nfse_envio(self, doc_numero):
        """
        Monta o documento XML para cancelamento da NFS-e.
        """
        cancelar_nfse_obj = cancelar_nfse.CancelarNfseEnvio(
            pedido=TcPedidoCancelamento(
                inf_pedido_cancelamento=TcInfPedidoCancelamento(
                    id=doc_numero,
                    identificacao_nfse=TcIdentificacaoNfse(
                        numero=doc_numero,
                        cnpj=self.cnpj_prestador,
                        inscricao_municipal=self.im_prestador,
                        codigo_municipio=self.cidade
                    ),
                    codigo_cancelamento='0001'
                )
            )
        )
        return cancelar_nfse_obj

    def consulta_nfse_rps(self, **kwargs):
        """
        Consulta da NFS-e por RPS, utilizando a comunicação SOAP do XSDATA.
        """
        rps_numero = kwargs.get('rps_number')
        rps_serie = kwargs.get('rps_serie')
        rps_tipo = kwargs.get('rps_type')

        servico = self._servicos[self.consulta_nfse_rps.__name__]
        client = Client.from_service(
            ConsultarNeporRpsConsultarNfsePorRpsEnvio,
            location=self._get_location(servico)
        )

        session = self._transmissao.session
        transport = DefaultTransport(session=session)
        client.transport = transport

        consultar_nfse_por_rps_envio = self._prepara_consultar_nfse_rps(
            rps_numero,
            rps_serie,
            rps_tipo,
        )
        cconsultar_input = ConsultarNeporRpsConsultarNfsePorRpsEnvioInput(
            body=ConsultarNeporRpsConsultarNfsePorRpsEnvioInput.Body(
                consultar_nfse_por_rps_envio
            )
        )
        consultar_output: ConsultarNeporRpsConsultarNfsePorRpsEnvioOutput
        consultar_output = client.send(cconsultar_input)

        # Extrai apenas a parte relevante do envelope SOAP.
        consultar_nfse_por_rps_reposta = (
            consultar_output.body
            .consultar_nfse_por_rps_envio_response
            .consultar_nfse_rps_resposta
        )
        config = SerializerConfig(pretty_print=True)
        serializer = XmlSerializer(config=config)

        xml_input = serializer.render(consultar_nfse_por_rps_envio)
        xml_output = serializer.render(consultar_nfse_por_rps_reposta)

        return RetornoSoap(
            webservice=servico.operacao,
            raiz=consultar_nfse_por_rps_envio,
            xml=xml_input,
            retorno=xml_output,
            resposta=consultar_nfse_por_rps_reposta
        )

    def _prepara_consultar_nfse_rps(self, rps_numero, rps_serie, rps_tipo):
        raiz = ConsultarNfsePorRpsEnvio(
            identificacao_rps=TcIdentificacaoRps(
                numero=rps_numero,
                serie=rps_serie,
                tipo=rps_tipo,
            ),
            prestador=TcIdentificacaoPrestador(
                cnpj=self.cnpj_prestador,
                inscricao_municipal=self.im_prestador
            ),
        )
        return raiz

    def sign(self, obj: any, ref_id=None):
        """
        This function takes an input dataclass instance,
        serializes it into an XML string, signs the resulting XML using the
        provided certificate and key, and returns the signed XML as an lxml element tree.

        :param obj: The input dataclass instance to be signed.
        :param ref_id: (Optional) Id of the signature reference element if needed.

        :return: An lxml ElementTree containing the signed XML data.
        """
        # TODO Implementar essa alteração no eprbrasil.edoc e erpbrasil.assinatura.
        serializer = XmlSerializer(config=SerializerConfig(
            xml_declaration=False
        ))
        xml_string = serializer.render(obj=obj)
        xml_etree = etree.fromstring(xml_string.encode('utf-8'))
        _cert = self._transmissao.certificado._cert
        _key = self._transmissao.certificado._chave
        signer = XMLSignerWithSHA1(
            method=signxml.methods.enveloped,
            signature_algorithm="rsa-sha1",
            digest_algorithm='sha1',
            c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
        )
        signer.excise_empty_xmlns_declarations = True
        signer.namespaces = {None: signxml.namespaces.ds}
        root = signer.sign(
            data=xml_etree,
            key=_key,
            cert=_cert,
            reference_uri=f"#{ref_id}" if ref_id else None
        )
        return root

    def _get_location(self, servico):
        """
        Join webservice base URL with specific service.
        """
        return urljoin(self._url, servico.endpoint)
