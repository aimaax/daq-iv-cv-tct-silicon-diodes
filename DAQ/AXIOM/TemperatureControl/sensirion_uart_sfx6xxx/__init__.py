#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
from os import path
from .version import version as __version__  # noqa: F401

from .device import Sfx6xxxDevice  # noqa: F401

__all__ = ['Sfx6xxxDevice']
