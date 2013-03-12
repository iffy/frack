from zope.interface import Interface, Attribute



class ITicketStore(Interface):


    def fetchTicket(number):
        """
        @param number: Ticket number

        @return: A dictionary of ticket data.
        """
