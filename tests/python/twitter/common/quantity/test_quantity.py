# ==================================================================================================
# Copyright 2011 Twitter, Inc.
# --------------------------------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==================================================================================================

import pytest
from twitter.common.quantity import Amount, Time, Data

def test_equals():
  assert Amount(1, Time.DAYS) == Amount(1, Time.DAYS), \
    "identical amounts should be equal"

  assert Amount(1, Time.DAYS) == Amount(24, Time.HOURS), \
    "expected equality to be calculated from amounts converted to a common unit"

  assert Amount(25, Time.HOURS) != Amount(1, Time.DAYS), \
    "expected unit conversions to not lose precision"

  assert Amount(1, Time.DAYS) != Amount(25, Time.HOURS), \
    "expected unit conversions to not lose precision"

  with pytest.raises(TypeError):
    Amount(1, Time.NANOSECONDS) == Amount(1, Data.BYTES)


def test_comparison_mixed_units():
  assert Amount(1, Time.MINUTES) > Amount(59, Time.SECONDS)
  assert Amount(1, Time.MINUTES) == Amount(60, Time.SECONDS)
  assert Amount(1, Time.MINUTES) < Amount(61, Time.SECONDS)

  assert Amount(59, Time.SECONDS) < Amount(1, Time.MINUTES)
  assert Amount(60, Time.SECONDS) == Amount(1, Time.MINUTES)
  assert Amount(61, Time.SECONDS) > Amount(1, Time.MINUTES)


def test_sorting():
  elements = [1, 2, 3, 4]
  elements_unsorted = [2, 4, 1, 3]

  def map_to_amount(amtlist):
    return [Amount(x, Time.MILLISECONDS) for x in amtlist]

  assert map_to_amount(elements) == sorted(map_to_amount(elements_unsorted))


def test_reduction():
  minute = Amount(60, Time.SECONDS)
  assert minute._amount == 1 and minute._unit == Time.MINUTES


def test_add():
  kb = Amount(512, Data.BYTES) + Amount(1536, Data.BYTES)
  assert kb._amount == 2 and kb._unit == Data.KB
  kb = kb + Amount(1, Data.BYTES)
  assert kb._amount == 2049 and kb._unit == Data.BYTES

  # disparate units
  value = Amount(1, Data.KB) + Amount(1, Data.MB)
  assert value._amount == 1025
  assert value._unit == Data.KB

def test_mul():
  assert 5 * Amount(12, Time.SECONDS) == Amount(12, Time.SECONDS) * 5
  amount = 5 * Amount(12, Time.SECONDS)
  assert amount._amount == 1 and amount._unit == Time.MINUTES
