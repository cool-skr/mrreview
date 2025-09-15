// This is a fake secret for testing purposes
const SUPER_SECRET_TOKEN = "a_very_long_and_obviously_fake_secret_token_for_javascript_testing_54321";

/**
 * This is a well-documented function that prints a greeting.
 * It uses the standard JSDoc format.
 * @param {string} name - The name to greet.
 */
function wellDocumentedFunction(name) {
    console.log(`Hello, ${name}!`);
}

function undocumentedFunction(x, y) {
    return x + y;
}


function overlyComplexFunction(h) {
    if (h) {
        if (h) {
            if (h) {
                if (h) {
                    if (h) {
                        if (h) {
                            if (h) {
                                if (h) {
                                    if (h) {
                                        if (h) {
                                            if (h) {
                                                console.log("ok");
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

/**
 * A function containing a classic performance anti-pattern.
 * @param {Array<any>} myArray - An array of items to concatenate.
 * @returns {string} The concatenated string.
 */
function inefficientStringBuilder(myArray) {
    let finalString = "";
    for (const item of myArray) {
        finalString += item + ",";
    }
    return finalString;
}

const anUnusedVariable = "This should be flagged by ESLint";


wellDocumentedFunction("World");
undocumentedFunction(1, 2);
overlyComplexFunction(true);
inefficientStringBuilder(['a', 'b', 'c']);