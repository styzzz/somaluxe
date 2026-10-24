from . import administration, inventory, marketing, orders, sales

MODULES = {
    "sales": sales,
    "order_operations": orders,
    "marketing_growth": marketing,
    "inventory_storage": inventory,
    "administration": administration,
}


def all_tools(backend, queue):
    return [t for m in MODULES.values() for t in m.tools(backend, queue)]
