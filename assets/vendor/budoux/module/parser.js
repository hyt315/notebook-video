/**
 * @license
 * Copyright 2021 Google LLC
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/**
 * Base BudouX parser.
 */
export class Parser {
    /**
     * Constructs a BudouX parser.
     * @param model A model data.
     */
    constructor(model) {
        this.model = new Map(Object.entries(model).map(([k, v]) => [
            k,
            new Map(Object.entries(v)),
        ]));
        this.baseScore =
            -0.5 *
                [...this.model.values()]
                    .flatMap((group) => [...group.values()])
                    .reduce((prev, curr) => prev + curr, 0);
    }
    /**
     * Parses the input sentence and returns a list of semantic chunks.
     *
     * @param sentence An input sentence.
     * @return The retrieved chunks.
     */
    parse(sentence) {
        if (sentence === '')
            return [];
        const boundaries = this.parseBoundaries(sentence);
        const result = [];
        let start = 0;
        for (const boundary of boundaries) {
            result.push(sentence.slice(start, boundary));
            start = boundary;
        }
        result.push(sentence.slice(start));
        return result;
    }
    /**
     * Parses the input sentence and returns a list of boundaries.
     *
     * @param sentence An input sentence.
     * @return The list of boundaries.
     */
    parseBoundaries(sentence) {
        const result = [];
        const uw1 = this.model.get('UW1');
        const uw2 = this.model.get('UW2');
        const uw3 = this.model.get('UW3');
        const uw4 = this.model.get('UW4');
        const uw5 = this.model.get('UW5');
        const uw6 = this.model.get('UW6');
        const bw1 = this.model.get('BW1');
        const bw2 = this.model.get('BW2');
        const bw3 = this.model.get('BW3');
        const tw1 = this.model.get('TW1');
        const tw2 = this.model.get('TW2');
        const tw3 = this.model.get('TW3');
        const tw4 = this.model.get('TW4');
        for (let i = 1; i < sentence.length; i++) {
            let score = this.baseScore;
            // NOTE: Score values in models may be negative.
            score += (uw1 === null || uw1 === void 0 ? void 0 : uw1.get(sentence.substring(i - 3, i - 2))) || 0;
            score += (uw2 === null || uw2 === void 0 ? void 0 : uw2.get(sentence.substring(i - 2, i - 1))) || 0;
            score += (uw3 === null || uw3 === void 0 ? void 0 : uw3.get(sentence.substring(i - 1, i))) || 0;
            score += (uw4 === null || uw4 === void 0 ? void 0 : uw4.get(sentence.substring(i, i + 1))) || 0;
            score += (uw5 === null || uw5 === void 0 ? void 0 : uw5.get(sentence.substring(i + 1, i + 2))) || 0;
            score += (uw6 === null || uw6 === void 0 ? void 0 : uw6.get(sentence.substring(i + 2, i + 3))) || 0;
            score += (bw1 === null || bw1 === void 0 ? void 0 : bw1.get(sentence.substring(i - 2, i))) || 0;
            score += (bw2 === null || bw2 === void 0 ? void 0 : bw2.get(sentence.substring(i - 1, i + 1))) || 0;
            score += (bw3 === null || bw3 === void 0 ? void 0 : bw3.get(sentence.substring(i, i + 2))) || 0;
            score += (tw1 === null || tw1 === void 0 ? void 0 : tw1.get(sentence.substring(i - 3, i))) || 0;
            score += (tw2 === null || tw2 === void 0 ? void 0 : tw2.get(sentence.substring(i - 2, i + 1))) || 0;
            score += (tw3 === null || tw3 === void 0 ? void 0 : tw3.get(sentence.substring(i - 1, i + 2))) || 0;
            score += (tw4 === null || tw4 === void 0 ? void 0 : tw4.get(sentence.substring(i, i + 3))) || 0;
            if (score > 0)
                result.push(i);
        }
        return result;
    }
}
//# sourceMappingURL=parser.js.map