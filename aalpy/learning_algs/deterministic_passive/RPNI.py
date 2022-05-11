import time
from bisect import insort

from aalpy.learning_algs.deterministic_passive.rpni_helper_functions import to_automaton, createPTA, \
    check_sequance, extract_unique_sequences


class RPNI:
    def __init__(self, data, automaton_type, print_info=True):
        self.data = data
        self.automaton_type = automaton_type
        pta_construction_start = time.time()
        self.root_node = createPTA(data, automaton_type)
        self.test_data = extract_unique_sequences(self.root_node)
        if print_info:
            print(f'PTA Construction Time: {round(time.time() - pta_construction_start, 2)}')
        self.print_info = print_info

    def run_rpni(self):
        start_time = time.time()

        red = [self.root_node]
        blue = list(red[0].children.values())

        while blue:
            lex_min_blue = min(list(blue), key=lambda x: len(x.prefix))
            merged = False

            for red_state in red:
                merge_candidate = self._merge(red_state, lex_min_blue, copy_nodes=True)
                if self._compatible(merge_candidate):
                    self._merge(red_state, lex_min_blue)
                    merged = True
                    break

            if not merged:
                insort(red, lex_min_blue)
                if self.print_info:
                    print(f'\rCurrent automaton size: {len(red)}', end="")

            blue.clear()
            for r in red:
                for c in r.children.values():
                    if c not in red:
                        blue.append(c)

        if self.print_info:
            print('')
            print(f'RPNI Learning Time: {round(time.time() - start_time, 2)}')
            print(f'RPNI Learned {len(red)} state automaton.')

        assert sorted(red, key=lambda x: len(x.prefix)) == red
        return to_automaton(red, self.automaton_type)

    def _compatible(self, r):
        for sequence in self.test_data:
            if not check_sequance(r, sequence, automaton_type=self.automaton_type):
                return False
        return True

    def _merge(self, r, lex_min_blue, copy_nodes=False):
        root_node = self.root_node.copy() if copy_nodes else self.root_node
        lex_min_blue = lex_min_blue.copy() if copy_nodes else lex_min_blue

        red_node = root_node
        for p in r.prefix:
            red_node = red_node.children[p]

        b_prefix = lex_min_blue.prefix
        to_update = root_node
        for p in b_prefix[:-1]:
            to_update = to_update.children[p]

        to_update.children[b_prefix[-1]] = red_node
        if self.automaton_type != 'mealy':
            self._fold(red_node, lex_min_blue)
        else:
            self._fold_mealy(red_node, lex_min_blue)

        return root_node

    def _fold(self, red_node, blue_node):
        red_node.output = blue_node.output

        for i in blue_node.children.keys():
            if i in red_node.children.keys():
                self._fold(red_node.children[i], blue_node.children[i])
            else:
                red_node.children[i] = blue_node.children[i].copy()

    def _fold_mealy(self, red_node, blue_node):
        blue_io_map = {i: o for i, o in blue_node.children.keys()}

        updated_keys = {}
        for io, val in red_node.children.items():
            o = blue_io_map[io[0]] if io[0] in blue_io_map.keys() else io[1]
            updated_keys[(io[0], o)] = val
        red_node.children = updated_keys

        for i in blue_node.children.keys():
            if i in red_node.children.keys():
                self._fold(red_node.children[i], blue_node.children[i])
            else:
                red_node.children[i] = blue_node.children[i].copy()


def run_RPNI(data, automaton_type):
    """
    Run RPNI, a deterministic passive model learning algorithm.
    Resulting model conforms to the provided data.
    For more informations on RPNI, check out AALpy' Wiki:
    https://github.com/DES-Lab/AALpy/wiki/RPNI---Passive-Deterministic-Automata-Learning

    Args:

        data: sequance of input output sequences. Eg. [[(i1,o1), (i2,o2)], [(i1,o1), (i1,o2), (i3,o1)], ...]
        automaton_type: either 'dfa', 'mealy', 'moore'

    Returns:

        Model conforming to the data.
    """
    assert automaton_type in {'dfa', 'mealy', 'moore'}
    return RPNI(data, automaton_type).run_rpni()
