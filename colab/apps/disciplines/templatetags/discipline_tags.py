from django import template
from mptt.utils import drilldown_tree_for_node, tree_item_iterator

register = template.Library()
