from collections import defaultdict

# import and configure matplotlib library
try:
#    os.environ['HOME'] = settings.MATPLOTLIB_HOME
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as pyplot
    from matplotlib.pyplot import legend
    is_matplotlib_imported = True
    from mpl_toolkits.mplot3d import Axes3D

except ImportError:
    is_matplotlib_imported = False



class Node():
    def __init__(self, children, sch, value_dicts, value_keys, graph_info):
        self.sch = sch
        self.value_dicts = value_dicts
        self.value_keys = value_keys
        self.graph_info = graph_info
        self.children = children

    def get_children(self):
        for children in self.children:
            yield children

    def get_schema(self):
        return self.sch

class ExperimentList(Node):
    pass

class Experiment(Node):
    pass

class Dataset(Node):
    pass

class Datafile(Node):
    pass


def graph(name, node, plots):

    #fig = matplotlib.pyplot.figure()
    fig = matplotlib.pyplot.gcf()
    #fig.set_size_inches(15.5, 13.5)
    print "plots=%s" % plots
    colors = ['blue', 'red']
    ax = None
    for i, plot in enumerate(plots):
        print "plot=%s" % plot
        vals = []
        for j, coord in enumerate(plot):
            if not j:
                if plot[0]:
                    label = str(plot[0])
                else:
                    label = None
                continue
            print "coord=%s" % str(coord)
            vals.append(coord[1])

        print "vals=%s" % vals

        if not ax:
            if len(vals) == 3:
                ax = Axes3D(fig)
                #ax = fig.gca(projection='3d')
            else:
                ax = fig.add_subplot(111, frame_on=False)

        if vals:
            ax.scatter(*vals, color=colors[i],  marker="x", label=label)

    if ax:
        info = node.graph_info
        if 'axes' in info:
            pyplot.xlabel(info['axes'][0])
            pyplot.ylabel(info['axes'][1])

        pyplot.grid(True)
        #legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        ax.legend()
        #pyplot.xlim(xmin=0)

        matplotlib.pyplot.savefig("graphout/%s.png" % name, dpi=100)
        matplotlib.pyplot.close()



def get_graph(node, functions):
    parameterset = node
    #for parameterset in node:
    # if parameterset.schema not in hrmc_schemas:
    #     continue
    schema = parameterset.sch
    value_dict = parameterset.value_dicts
    print value_dict
    value_keys = parameterset.value_keys
    print value_keys
    graph_info = parameterset.graph_info
    print graph_info


    plots = []
    for i, key in enumerate(value_keys):
        print "key=%s" % key
        # find values from children
        graph_vals = defaultdict(list)
        for child in node.get_children():
            print "child=%s" % child
            child_val = child.value_dicts
            print "child_val=", child_val
            for k in child_val:
                print "k=", k
                if k in key:
                    if isinstance(child_val[k], basestring):
                        print child_val[k]
                        if child_val[k] in functions:
                            graph_vals[k].extend(functions[child_val[k]])
                        else:
                            graph_vals[k].append(child_val[k])
                    elif isinstance(child_val[k], (int,long)):
                        graph_vals[k].append(child_val[k])
                    else:
                        for l in list(child_val[k]):
                            graph_vals[k].append(l)
                else:
                    pass

        #find constants from node via value_keys
        i=0
        for x in key:
            if '/' not in x:
                if isinstance(x, basestring):
                    if x in functions:
                         graph_vals[x].extend(functions[x])
                    else:
                         print "Cannot resolve %s in reference %s" % (x, key)
                    #graph_vals["%s/%s" % (schema, i)].append(functions[x])
                    i += 1
                elif isinstance(x, (int,long)):
                    graph_vals[x].append(int(x))
                else:
                    pass
                    # for y in list(x):
                    #     graph_vals["%s/%s" % (schema,i)].append(y)
                    # i += 1

        #find constants from node via value_dict
        for k,v in value_dict.items():
            if k in key:
                if isinstance(v, basestring):
                    if '/' not in v:
                        if v in functions:
                            graph_vals[k].extend(functions[v])
                        else:
                            print "cannot resolve %s:%s in reference %s" % (k, v, key)
                    else:
                        graph_vals[k].append(v)
                elif isinstance(v, (int,long)):
                    graph_vals[k].append(v)
                else:
                    for l in list(v):
                        graph_vals[k].append(l)

        # reorder based on value_keys
        res = []
        if 'legends' in graph_info:
            res.append(graph_info['legends'][i])
        else:
            res.append([])
        i = 0
        for k in key:
            if isinstance(k, basestring):
                res.append((k, graph_vals[k]))
            elif isinstance(k, (int,long)):
                res.append((k, graph_vals[k]))
            else:
                key = "%s/%s" % (schema, i)
                res.append((key, graph_vals[key]))
                i += 1

        plots.append(res)


    return (plots)


if __name__ == '__main__':

    data = {}

    data['datafile8'] = Datafile([],
        'df1',
        {'df1/s':5, 'df1/v': 5},
        [[]],
        {})

    data['datafile9'] = Datafile([],
        'df1',
        {'df1/s':6, 'df1/v': 7, 'df1/x':[3]},
        [['df1/x', 'df1/v']],
        {})

    data['datafile10'] = Datafile([],
        'df1',
        {'df1/s':8, 'df1/v': 9},
        [[]],
        {})

    data['datafile11'] = Datafile([],
        'df1',
        {'df1/s':10, 'df1/v': 23},
        [[]],
        {})

    data['datafile12'] = Datafile([],
        'df1',
        {'df1/s':12, 'df1/v': 24},
        [[]],
        {})

    data['datafile13'] = Datafile([],
        'df1',
        {'df1/s':13, 'df1/v': 25},
        [[]],
        {})

    data['datafile14'] = Datafile([],
        'df2',
        {'df2/s':14, 'df2/v': 26},
        [[]],
        {})

    data['datafile15'] = Datafile([],
        'df2',
        {'df2/s':1, 'df2/v': 32, 'df2/xx': 'tardis.tardis_portal.filters.getdf'},
        [[]],
        {})

    data['datafile16'] = Datafile([],
        'df2',
        {'df2/s':7, 'df2/v': 11},
        [[]],
        {})

    data['datafile17'] = Datafile([],
        'df3',
        {'df3/s':14, 'df3/v': 65, 'df3/x': 11},
        [[]],
        {})


    data['datafile18'] = Datafile([],
        'df3',
        {'df3/s':7, 'df3/v': 65, 'df3/x': 11},
        [],
        {})

    data['datafile19'] = Datafile([],
        'df3',
        {'df3/s': 'tardis.tardis_portal.filters.getdf', 'df3/v': [65,66,67,69], 'df3/x': 11},
        [
            ['tardis.tardis_portal.filters.x', 'df3/s', 'df3/s'],
            ['tardis.tardis_portal.filters.y', 'df3/s', 'df3/s'],
        ],
        {})

    data['dataset4'] = Dataset([data['datafile8'], data['datafile9'], data['datafile10'], data['datafile11'], data['datafile12'], data['datafile13'], data['datafile14']],
        'ds1',
        {'ds1/a': 214, 'ds1/b': 3.322, 'ds1/val': 589, 'ds1/val2': 90, 'ds1/it':1},
        [['df1/s', 'df1/v']],
        {})


    data['dataset5'] = Dataset([data['datafile15'], data['datafile16'], data['datafile17']],
        'ds1',
        {'ds1/a': 21, 'ds1/b': 8.53, 'ds1/val': [0,2,5,7,9], 'ds1/val2': 22, 'ds1/it': 0},
        [['df2/s', 'df2/v'], ['tardis.tardis_portal.filters.x', 'df2/xx']],
        {'legends': ['value1', 'extractvalues']})


    data['dataset6'] = Dataset([],
        'ds2',
        {'ds2/a': [2,5,7], 'ds2/b': [3,57,50.53], 'ds2/val': 21, 'ds2/val2': 22, 'ds2/it': 1},
        [['ds2/a', 'ds2/b']],
        {})


    data['dataset7'] = Dataset([data['datafile18']],
        'ds2',
        {'ds2/a': 21, 'ds2/b': 433, 'ds2/val': 22, 'ds2/val2': 23, 'ds2/it': 2},
        [['df3/s', 'df3/v']],
        {})

    data['dataset8'] = Dataset([data['datafile19']],
        'ds2',
        {'ds2/a': 21, 'ds2/b': 433, 'ds2/val': 213, 'ds2/val2': 23, 'ds2/it': 4},
        [['df3/s', 'df3/v']],
        {})

    data['experiment1'] = Experiment([data['dataset4']],
        'exp1',
        {'exp1/x': 12, 'exp1/y': 13, 'exp1/val': 34, 'exp1/a': [11,14,17,22]},
        [['ds1/it', 'ds1/val']],
        {'legends':['value1']}
    )

    data['experiment2'] = Experiment([data['dataset5']],
        'exp1',
        {'exp1/x': 3, 'exp1/y': 12, 'exp1/val': 32, 'exp1/a': 3, 'exp1/cons': [1,5,5,5,9]},
        [['ds1/val', 'exp1/cons']],
       {'legends':['value1']}
    )

    data['experiment3']  = Experiment([data['dataset6'], data['dataset7']],
        'exp2',
        {'exp2/x': [14,15], 'exp2/y': 11, 'exp2/val': [23, 24]},
        [['ds2/it','ds2/val2', 'exp2/val'], ['ds2/it', 'exp2/val', 'exp2/val']] ,
        {}
    )

    data['experiment3b']  = Experiment([],
        'exp3',
        {'exp3/x': [0,2,3,6], 'exp3/y': 13, 'exp3/val': 3124, 'exp3/val2': [3,4,6,13], "exp3/id": [1,2,3,4]},
        [['exp3/id','exp3/val2']],
        {'legends':['value1']}
)

    data['experimentlist0'] = ExperimentList([data['experiment1'], data['experiment2']],
        'explist1',
        {},
        [['exp1/x', 'exp1/y', 'exp1/val']],
        {'axes': ['x','y','val']}
        )

    data['experimentlist0b'] = ExperimentList([data['experiment3']],
        'explist2',
        {},
        [['exp2/x', 'exp2/val']],
        {})

    functions = {
        'tardis.tardis_portal.filters.getdf': [1,3,5,7], #only works for lists
        'tardis.tardis_portal.filters.x': [2,4,6,8],
        'tardis.tardis_portal.filters.y': [11,14,15,35],
    }

    for node in ('experimentlist0', 'experimentlist0b', 'experiment1', 'experiment2', 'experiment3', 'experiment3b', 'dataset4', 'dataset5', 'dataset6', 'dataset7', 'dataset8', 'datafile8', 'datafile9', 'datafile10', 'datafile15', 'datafile19'):
    #for node in ('dataset7',):

        plots = get_graph(data[node], functions)
        print "%s = %s" % (node, plots)
        graph(node, data[node], plots)


