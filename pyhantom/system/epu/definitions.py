from pyhantom.phantom_exceptions import PhantomAWSException
import simplejson as json

g_definition_key_name = "PHANTOM_DEFINTION"
g_default_definition = "single_site_n_preserving"

g_add_template = {
                  'engine_conf':
                    {'preserve_n': None,
                     'epuworker_type': None}
                  }
single_site_n_preserving_definition = {
    'general' : {
        'engine_class' : 'epu.decisionengine.impls.phantom.PhantomSingleSiteEngine',
        },
    'health' : {
        'monitor_health' : False
    }
}

g_test_def_types = {
    'number': int,
    'string': str
}
g_test_def_definition = {
    'general' : {
        'engine_class' : 'epu.decisionengine.impls.phantom.PhantomSingleSiteEngine',
    },
    'health' : {
        'monitor_health' : False
    }
}


n_preserving_types = {
}
single_site_n_preserving_definition = {
    'general' : {
        'engine_class' : 'epu.decisionengine.impls.phantom.PhantomSingleSiteEngine',
    },  
    'health' : {
        'monitor_health' : False
    }
}


def validate_cloud(cloud_string):

    la = cloud_string.split(':')
    if len(la) != 2:
        raise PhantomAWSException('InvalidParameterValue', details="The format is <cloud site name>:<integer size>.  You sent %s" % (cloud_string))
    (site_name, n_vms) = la

    try:
        int(n_vms)
    except Exception, ex:
        raise PhantomAWSException('InvalidParameterValue', details="The format is <cloud site name>:<integer size>.  You sent %s" % (cloud_string))

    result_doc = {'site_name': site_name, 'size': n_vms}
    return result_doc


multi_site_n_preserving_types = {
    'cloud': validate_cloud,
}
multi_site_n_preserving_definition = {
    'general' : {
        'engine_class' : 'epu.decisionengine.impls.phantom.PhantomMultiSiteEngine',
    },
    'health' : {
        'monitor_health' : False
    }
}

def ordered_cloud_list(cloud_list_string):
    c_l = cloud_list_string.split(",")

    rank = 1
    ordered_list = []

    for cloud in c_l:
        res_doc = validate_cloud(cloud)
        res_doc['rank'] = rank
        rank = rank + 1
        ordered_list.append(res_doc)
    
    return ordered_list

error_overflow_n_preserving_types = {
    'clouds': ordered_cloud_list,
    'n_preserve': int,
}
error_overflow_n_preserving_definition = {
    'general' : {
        'engine_class' : 'epu.decisionengine.impls.phantom_multi_site_overflow.PhantomMultiSiteOverflowEngine',
    },
    'health' : {
        'monitor_health' : False
    }
}

g_known_definitions = {
    "test": g_test_def_definition,
    "single_site_n_preserving": single_site_n_preserving_definition,
    "multi_site_n_preserving": multi_site_n_preserving_definition,
    "error_overflow_n_preserving": error_overflow_n_preserving_definition
    }
g_known_templates = {
    "test": g_test_def_types,
    "single_site_n_preserving": n_preserving_types,
    "multi_site_n_preserving": multi_site_n_preserving_types,
    "error_overflow_n_preserving": error_overflow_n_preserving_types
}


def tags_to_definition(Tags):
    definition_name = g_default_definition
    parameters = {}

    # this first loop simply eliminates the need to have the definition be the first entry
    for tag in Tags:
        if tag.Key == g_definition_key_name:
            definition_name = tag.Value
        else:
            parameters[tag.Key] = tag.Value

    # this next call may later be replaced by a call to the epu system
    if definition_name not in g_known_templates.keys():
        raise PhantomAWSException('InvalidParameterValue', details="%s is an unknown definition type.  Please check your tags" % (definition_name))
    def_template = g_known_templates[definition_name]

    result_doc = {}
    for p in parameters:
        if p not in def_template:
            raise PhantomAWSException('InvalidParameterValue', details="%s does not take a parameter of %s.  Please check your tags" %(definition_name, p))

        try:
            val = def_template[p](parameters[p])
        except PhantomAWSException, paex:
            raise
        except Exception:
            raise PhantomAWSException('InvalidParameterValue', details="The tag %s has a value %s that could not be understood.  Please check the type" % (p, parameters[p]))

        result_doc[p] = val

    return (definition_name, result_doc)


def load_known_definitions(epum_def_client):
    domain_def_list = epum_def_client.list_domain_definitions()
    for domain_def in g_known_definitions:
        if domain_def not in domain_def_list:
            epum_def_client.add_domain_definition(domain_def, g_known_definitions[domain_def])
