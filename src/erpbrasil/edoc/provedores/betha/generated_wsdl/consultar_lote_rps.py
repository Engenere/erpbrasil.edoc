"""This file was generated by xsdata, v23.8, on 2023-10-18 21:20:30

Generator: DataclassGenerator
See: https://xsdata.readthedocs.io/
"""
from dataclasses import dataclass, field
from typing import Optional
from .consultar_nfse import TcListaNfse
from .recepcionar_lote_rps import (
    TcIdentificacaoPrestador,
    TcListaMensagemRetorno,
)

__NAMESPACE__ = "http://www.betha.com.br/e-nota-contribuinte-ws"


@dataclass
class ConsultarLoteRpsEnvio:
    class Meta:
        namespace = "http://www.betha.com.br/e-nota-contribuinte-ws"

    prestador: Optional[TcIdentificacaoPrestador] = field(
        default=None,
        metadata={
            "name": "Prestador",
            "type": "Element",
            "namespace": "",
        }
    )
    protocolo: Optional[int] = field(
        default=None,
        metadata={
            "name": "Protocolo",
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass
class ConsultarNotaResp:
    class Meta:
        name = "consultarNotaResp"

    lista_nfse: Optional[TcListaNfse] = field(
        default=None,
        metadata={
            "name": "ListaNfse",
            "type": "Element",
            "namespace": "",
        }
    )
    lista_mensagem_retorno: Optional[TcListaMensagemRetorno] = field(
        default=None,
        metadata={
            "name": "ListaMensagemRetorno",
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass
class ConsultarLoteRpsEnvioResponse:
    class Meta:
        namespace = "http://www.betha.com.br/e-nota-contribuinte-ws"

    consultar_lote_rps_resposta: Optional[ConsultarNotaResp] = field(
        default=None,
        metadata={
            "name": "ConsultarLoteRpsResposta",
            "type": "Element",
            "namespace": "",
        }
    )


@dataclass
class ConsultarLoteRpsConsultarLoteRpsEnvioInput:
    class Meta:
        name = "Envelope"
        namespace = "http://schemas.xmlsoap.org/soap/envelope/"

    body: Optional["ConsultarLoteRpsConsultarLoteRpsEnvioInput.Body"] = field(
        default=None,
        metadata={
            "name": "Body",
            "type": "Element",
        }
    )

    @dataclass
    class Body:
        consultar_lote_rps_envio: Optional[ConsultarLoteRpsEnvio] = field(
            default=None,
            metadata={
                "name": "ConsultarLoteRpsEnvio",
                "type": "Element",
                "namespace": "http://www.betha.com.br/e-nota-contribuinte-ws",
            }
        )


@dataclass
class ConsultarLoteRpsConsultarLoteRpsEnvioOutput:
    class Meta:
        name = "Envelope"
        namespace = "http://schemas.xmlsoap.org/soap/envelope/"

    # Campo `header` Adicionado manualmente.
    # Embora o WSDL não faça menção a nenhum cabeçalho em sua definição,
    # o cabeçalho está sendo incluído na resposta SOAP.
    header: Optional[str] = field(
        default=None,
        metadata={
            "name": "Header",
            "type": "Element",
        }
    )

    body: Optional["ConsultarLoteRpsConsultarLoteRpsEnvioOutput.Body"] = field(
        default=None,
        metadata={
            "name": "Body",
            "type": "Element",
        }
    )

    @dataclass
    class Body:
        consultar_lote_rps_envio_response: Optional[ConsultarLoteRpsEnvioResponse] = field(
            default=None,
            metadata={
                "name": "ConsultarLoteRpsEnvioResponse",
                "type": "Element",
                "namespace": "http://www.betha.com.br/e-nota-contribuinte-ws",
            }
        )
        fault: Optional["ConsultarLoteRpsConsultarLoteRpsEnvioOutput.Body.Fault"] = field(
            default=None,
            metadata={
                "name": "Fault",
                "type": "Element",
            }
        )

        @dataclass
        class Fault:
            faultcode: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                }
            )
            faultstring: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                }
            )
            faultactor: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                }
            )
            detail: Optional[str] = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "",
                }
            )


class ConsultarLoteRpsConsultarLoteRpsEnvio:
    style = "document"
    location = "https://e-gov.betha.com.br/e-nota-contribuinte-test-ws/consultarLoteRps"
    transport = "http://schemas.xmlsoap.org/soap/http"
    input = ConsultarLoteRpsConsultarLoteRpsEnvioInput
    output = ConsultarLoteRpsConsultarLoteRpsEnvioOutput
