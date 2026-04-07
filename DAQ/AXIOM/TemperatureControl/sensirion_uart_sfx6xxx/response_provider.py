import struct
import sensirion_driver_adapters.mocks.response_provider as rp

 
class Sfx6xxxResponseProvider(rp.ResponseProvider):

    RESPONSE_MAP = {0xd0: {0: struct.pack('>64s', rp.random_ascii_string(64)),
                           1: struct.pack('>64s', rp.random_ascii_string(64)),
                           2: struct.pack('>64s', rp.random_ascii_string(64)),
                           3: struct.pack('>64s', rp.random_ascii_string(64))}
                    }

    def get_id(self) -> str:
        return 'Sfx6xxxResponseProvider'

    def handle_command(self, cmd_id: int, data: bytes, response_length: int) -> bytes:
        sub_cmd_map = self.RESPONSE_MAP.get(cmd_id, None)
        if sub_cmd_map is None:
            return rp.random_bytes(response_length)
        if None in sub_cmd_map:
            return sub_cmd_map[None]
        assert len(data) >= 1, "No subcommand specified!"
        actual_subcommand = data[0]
        return sub_cmd_map.get(actual_subcommand, rp.random_bytes(response_length))
