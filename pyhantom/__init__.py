from amqplib.client_0_8 import transport
XXX = transport.SSLTransport
import kombu.transport.amqplib
setattr(transport, 'SSLTransport', XXX)
