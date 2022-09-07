((window) => {
    const delegate = (root, selector, event, callback) => {
        root.addEventListener(event, e => {
            const closest = e.target.closest(selector);
            if (!closest) return;
            callback.apply(closest, [e]);
        });
    };

    const getByDot = (path = '', root) => {
        const parts = path.split(/(?<!\\)\./gi);
        while (parts.length) {
            root = root[parts.shift()];
            if (typeof root !== 'object' && parts.length > 1) {
                return void 0;
            }
        }
        return root;
    };

    const ifHTMLMatcher = /:if:(not:)?(\S+?):(?:(is|eq|lt|gt|lte|gte):(not:)?(\S+):)?([\s\S]*?)(?::else:\2:([\s\S]*?))?:endif:\2:/g;
    const eachHTMLMatcher = /:each:(\S+?):([\s\S]*?)(?::empty:\1:([\s\S]*?))?:endeach:\1:/g;
    const varHTMLMatcher = /:(\S+):/g;
    function render(template, state) {
        let output = template;
        // "Each" loops
        output = output.replace(eachHTMLMatcher, (match, prop, repeat, empty) => {
            const val = getByDot(prop, state);
            if (val instanceof Array && val.length) {
                return val.map((item, index) => {
                    const scope = {
                        ...item,
                        parent: state,
                        index
                    };
                    return render(repeat, scope);
                }).join('');
            } else {
                return empty || '';
            }
        });
        // "If" statements
        output = output.replace(ifHTMLMatcher, (match, not1, prop, operand, not2, check, pass, fail) => {
            const val = getByDot(prop, state);
            if (!not1 && check && operand) {
                if (operand === 'is') {
                    if ((not2 && check != val) || check == val) {
                        return pass ? render(pass, state) : '';
                    } else {
                        return fail ? render(fail, state) : '';
                    }
                } else {
                    const val2 = getByDot(check, state);
                    let result;
                    switch (operand) {
                        case 'eq':
                            result = val === val2;
                            break;
                        case 'lt':
                            result = val < val2;
                            break;
                        case 'lte':
                            result = val <= val2;
                            break;
                        case 'gt':
                            result = val > val2;
                            break;
                        case 'gte':
                            result = val >= val2;
                            break;
                    }
                    if (not2) {
                        result = !result;
                    }
                    if (result) {
                        return pass ? render(pass, state) : '';
                    } else {
                        return fail ? render(fail, state) : '';
                    }
                }
            }
            if ((not1 && (!val || !val.length)) ||
                ((val instanceof Array && val.length) || val)
            ) {
                return pass ? render(pass, state) : '';
            } else {
                return fail ? render(fail, state) : '';
            }
        });
        // Variables
        output = output.replace(varHTMLMatcher, (match, prop) => {
            const val = getByDot(prop, state);
            if (typeof val === 'object') {
                return JSON.stringify(val);
            }
            return val ?? '';
        });
        return output;
    };

    const mount = (template, state, tag) => {
        const r = () => morphdom(tag, `<div>${render(template, state)}</div>`, {childrenOnly: true});
        delegate(tag, '[data-call]', 'click', e => {
            const callKey = e.target.getAttribute('data-call');
            if (!(callKey in state)) {
                console.warn('[shum.js] Dumping current state:', state);
                throw new Error(`[shum.js] Missing event "${callKey}".`);
            } else {
                state[callKey](e, state);
                r();
            }
        });
        delegate(tag, '[data-bind]', 'click', e => {
            const bindKey = e.target.getAttribute('data-bind');
            const bool = ['checkbox', 'radio'].includes(e.target.getAttribute('type'));
            state[bindKey] = bool ? e.target.checked : e.target.value;
            r();
        });
        r();
        return r;
    };

    window.shum = {
        render,
        delegate,
        mount
    };
})(this);
