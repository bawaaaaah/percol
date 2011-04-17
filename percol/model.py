# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 mooz
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import types
import display
import debug

class SelectorModel(object):
    def __init__(self,
                 percol, collection, finder,
                 query = None, caret = None, index = None):
        self.percol = percol
        self.finder = finder(collection)
        self.setup_results(query)
        self.setup_caret(caret)
        self.setup_index(index)

    # ============================================================ #
    # Pager attributes
    # ============================================================ #

    @property
    def absolute_index(self):
        return self.index

    @property
    def results_count(self):
        return len(self.results)

    # ============================================================ #
    # Initializer
    # ============================================================ #

    def setup_results(self, query):
        self.query   = self.old_query = query or u""
        self.results = self.finder.get_results(self.query)
        self.marks   = [False] * self.results_count

    def setup_caret(self, caret):
        if isinstance(caret, types.StringType) or isinstance(caret, types.UnicodeType):
            try:
                caret = int(caret)
            except ValueError:
                caret = None
        if caret is None or caret < 0 or caret > display.display_len(self.query):
            caret = display.display_len(self.query)
        self.caret = caret

    def setup_index(self, index):
        if index is None or index == "first":
            self.select_top()
        elif index == "last":
            self.select_bottom()
        else:
            try:
                self.select_index(int(index))
            except:
                self.select_top()

    # ============================================================ #
    # Result handling
    # ============================================================ #

    def do_search(self, query):
        with self.percol.global_lock:
            self.index = 0
            self.results = self.finder.get_results(query)
            self.marks   = [False] * self.results_count

    def get_result(self, index):
        try:
            return self.results[index][0]
        except IndexError:
            return None

    def get_selected_result(self):
        return self.get_result(self.index)

    def get_selected_results_with_index(self):
        results = self.get_marked_results_with_index()
        if not results:
            try:
                index = self.index
                result = self.results[index]
                results.append((result[0], index, result[2]))
            except Exception as e:
                debug.log("get_selected_results_with_index", e)
        return results

    # ============================================================ #
    # Commands
    # ============================================================ #

    # ------------------------------------------------------------ #
    #  Selections
    # ------------------------------------------------------------ #

    def select_index(self, idx):
        if self.results_count > 0:
            self.index = idx % self.results_count
        else:
            self.index = 0

    def select_next(self):
        self.select_index(self.index + 1)

    def select_previous(self):
        self.select_index(self.index - 1)

    def select_top(self):
        self.select_index(0)

    def select_bottom(self):
        self.select_index(max(self.results_count - 1, 0))

    # ------------------------------------------------------------ #
    # Mark
    # ------------------------------------------------------------ #

    def get_marked_results_with_index(self):
        if self.marks:
            return [(self.results[i][0], i, self.results[i][2])
                    for i, marked in enumerate(self.marks) if marked]
        else:
            return []

    def toggle_mark(self):
        self.marks[self.index] ^= True

    def toggle_mark_and_next(self):
        self.toggle_mark()
        self.select_next()

    # ------------------------------------------------------------ #
    # Caret position
    # ------------------------------------------------------------ #

    def set_caret(self, caret):
        q_len = len(self.query)

        self.caret = max(min(caret, q_len), 0)

    def beginning_of_line(self):
        self.set_caret(0)

    def end_of_line(self):
        self.set_caret(len(self.query))

    def backward_char(self):
        self.set_caret(self.caret - 1)

    def forward_char(self):
        self.set_caret(self.caret + 1)

    # ------------------------------------------------------------ #
    # Text
    # ------------------------------------------------------------ #

    def append_char_to_query(self, ch):
        self.query += chr(ch).decode(self.percol.encoding)
        self.forward_char()

    def insert_char(self, ch):
        q = self.query
        c = self.caret
        self.query = q[:c] + chr(ch).decode(self.percol.encoding) + q[c:]
        self.set_caret(c + 1)

    def insert_string(self, string):
        caret_pos  = self.caret + len(string)
        self.query = self.query[:self.caret] + string + self.query[self.caret:]
        self.caret = caret_pos

    def delete_backward_char(self):
        if self.caret > 0:
            self.backward_char()
            self.delete_forward_char()

    def delete_forward_char(self):
        caret = self.caret
        self.query = self.query[:caret] + self.query[caret + 1:]

    def delete_end_of_line(self):
        self.query = self.query[:self.caret]

    def clear_query(self):
        self.query = u""

    # ------------------------------------------------------------ #
    # Text > kill
    # ------------------------------------------------------------ #

    def kill_end_of_line(self):
        self.killed = self.query[self.caret:]
        self.query  = self.query[:self.caret]

    killed = None                  # default
    def yank(self):
        if self.killed:
            self.insert_string(self.killed)

