class Player:
    def __init__(self, chat_id, player_id, player_name):
        self.chat_id = chat_id
        self.id = player_id
        self.name = player_name
        self.role = None
        self.special_role = None
        self.vote = None

    def print(self) -> str:
        out = str(self.chat_id) + ',' + str(self.id) + ',' + self.name
        if self.role is not None:
            out += ',' + self.role
        if self.special_role is not None:
            out += ',' + self.special_role
        return out

