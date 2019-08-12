import sys

class AHexDecConverter:
    '''
        Converts and encodes 14-bit decimal numbers to hexadecimal and 
        decodes hexadecimal representations to 14-bit decimal numbers.
    '''

    def CheckHex(self, hexcode):
        ''' Returns whether a two-char hexcode is valid or not '''
        hexString = str(hexcode)

        # First checks the length
        if len(hexString) != 2:
            return False

        # Then ensures the hexcode is valid
        try:
            int(hexString, 16)
        except:
            return False
        return True

    def CheckDec(self, decimalNumber):
        ''' Returns whether decimalNumber falls within our correct range '''
        if -8193 < decimalNumber < 8193:
            return True
        return False

    def Decode(self, hi, lo):
        '''
            Takes two bytes in the range [0x00..0x7F] and decodes them to a decimal representation.
        '''

        # Ensures hexcodes are valid
        try:
            hiBool = self.CheckHex(hi)
            loBool = self.CheckHex(lo)
            if not(hiBool and loBool):
                pass
                # raise ValueError("Decodable Hi and Lo hex values must each be represented by two characters between '00' and 'ff.'")
        except ValueError as error:
            sys.exit("ValueError: " + str(error))
        except Exception as e:
            sys.exit("Error: " + str(e))

        # Converts each decimal to integer, and shifts the hi byte left by 7 bits
        hi, lo = int(hi, 16) << 7, int(lo, 16) 

        # Returns the Combined bytes, where 8192 is subtracted so we're back in our signed range
        return (hi | lo) - 8192 

    def Encode(self, decNum):
        ''' 
            Removes sign from a given decimal, splits it into two bytes, 
            drops each byte's most significant bit (MSB), 
            then returns the 4-character representation of the number in hexadecimal format.
        '''

        # step 0: Ensures decimal number is actually an integer and is within range
        try:
            if not isinstance(decNum, int):
                raise TypeError("Encodable number must be an integer.")
            if not self.CheckDec(decNum):
                raise ValueError("Encodable number must be an integer between -8192 and 8192.")
        except TypeError as error:
            sys.exit("TypeError: " + str(error))
        except ValueError as error:
            sys.exit("ValueError: " + str(error))
        except Exception as error:
            sys.exit("Error: " + str(error))

        # step 1: adds 8192 to the decimal to make it unsigned
        decNum += 8192

        # step 2: pack into two bytes with most significant digits cleared
        hi, lo = decNum >> 7, decNum & 0x7f

        # Convert to hexadecimal
        hi, lo =  '{:02X}'.format(hi), '{:02X}'.format(lo)

        # step 3: return 4-character representation
        return (hi + lo)
