

#
#  
#
g_definition_name = "phantom0.1def"

g_definition = {
    'general' : {
        'engine_class' : 'epu.decisionengine.impls.phantom.PhantomEngine',
    },
    'health' : {
        'monitor_health' : False
    }
}


g_add_template = {
                  'engine_conf':
                    {'preserve_n': None,
                     'epuworker_type': None,
                     'force_site': None}
                  }


def get_definitions():
    pass

