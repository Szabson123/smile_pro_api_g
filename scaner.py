class Myback:

    name = "Szymon" 
    
    def say_hello(self):
        sent = "I m Szymon"
        return sent


    def say_no_hello(self):
        sent = "Im not Szymon"
        return sent

    def checker(self):
        check = input("Jak masz na imię")
        
        if check == self.name:
            print(self.say_hello())
            
        else:
            print(self.say_no_hello())
        

maback_instance = Myback()

maback_instance.checker()