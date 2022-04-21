class Player:

    def __init__(self, player_id, player_name, pronouns, role, special_role):
        self.id = player_id
        self.name = player_name
        self.pronouns = pronouns
        self.role = role
        self.special_role = special_role
        self.vote = None

    def print(self) -> str:
        out = str(self.id) + ',' + self.name + ',' + self.pronouns
        if self.role is not None:
            out += ',' + self.role
        if self.special_role is not None:
            out += ',' + self.special_role
        return out

