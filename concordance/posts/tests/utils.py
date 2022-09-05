import os
import inspect
import logging


logging.basicConfig(
    level=logging.DEBUG,
    filename=f"{os.path.dirname(os.path.realpath(__file__))}/debug_helper.log",
    filemode='w',
    datefmt=r'%H:%M:%S',
    format='%(asctime)s.%(msecs)03d\t%(name)s\t%(message)s')


def write_log(client, path, data, media, response):
    code = response.status_code
    caller = " -> ".join(
        call.function for call in reversed(inspect.stack()[1:3]))
    files = {f: os.listdir(os.path.join(media, f)) for f in os.listdir(media)}
    form = (response.context['form'] if response.context.get('form')
            else None)
    image = form.fields.get('image') if form else None
    valid = form.is_valid() if form else None
    errors = form.errors if form else None
    logging.info(f'CALL STACK: {caller}'
                 f'\t\tTEST CLIENT: {client.name}\n'
                 f'\tMEDIA_ROOT:\t{files}\n'
                 f'\tTargetURI:\t{path} -> [{code}]\n'
                 f'\tPOST Data:\t{data}\n'
                 f'\tImageField:\t{image}\n'
                 f'\tForm valid:\t{valid if not None else "No form"}\n'
                 f'\tErrorlist:\t{errors}')
