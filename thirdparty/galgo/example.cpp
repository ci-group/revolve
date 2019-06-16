//=================================================================================================
//                  Copyright (C) 2018 Alain Lanthier - All Rights Reserved  
//                  License: MIT License    See LICENSE.md for the full license.
//                  Original code 2017 Olivier Mallet (MIT License)              
//=================================================================================================

#include "Galgo.hpp"

//------------------------------------------------------------------
// Uncomment #define TEST_ALL_TYPE to test compiling of all types
// Uncomment #define TEST_BINAIRO to test GA for Binairos
//------------------------------------------------------------------
//#define TEST_ALL_TYPE
//#define TEST_BINAIRO

#include "TestFunction.hpp"

#ifdef TEST_ALL_TYPE
#include "TestTypes.hpp"
#endif


template <typename _TYPE>
void set_my_config(galgo::ConfigInfo<_TYPE>& config)
{
    // override some defaults
    config.mutinfo._sigma           = 1.0;
    config.mutinfo._sigma_lowest    = 0.01;
    config.mutinfo._ratio_boundary  = 0.10;

    config.covrate = 0.50;  // 0.0 if no cros-over
    config.mutrate = 0.05;
    config.recombination_ratio = 0.50;

    config.elitpop      = 5;
    config.tntsize      = 2;
    config.Selection    = TNT;
    config.CrossOver    = RealValuedSimpleArithmeticRecombination;
    config.mutinfo._type = galgo::MutationType::MutationGAM_UncorrelatedNStepSizeBoundary;

    config.popsize  = 100;
    config.nbgen    = 400;
    config.output   = true;
}

int main()
{  
#ifdef TEST_ALL_TYPE
    TEST_all_types();

    system("pause");
    return 0;
#endif

#ifdef TEST_BINAIRO
    system("color F0");
    GA_Binairo::test_ga_binairo(4);     // 0=resolve one free cell(hard), 1=resolve 4 free cells(very hard), 2=resolve 7 free cells(diabolical), 3 , 4==generate new grid

    system("pause");
    return 0;
#endif

    using _TYPE = float;    // Suppport float, double, char, int, long, ... for parameters
    const int NBIT = 32;    // Has to remain between 1 and 64

    // CONFIG
    galgo::ConfigInfo<_TYPE> config;        // A new instance of config get initial defaults
    set_my_config<_TYPE>(config);           // Override some defaults

    {
        {
            std::cout << std::endl;
            std::cout << "SumSameAsPrd function 2x2 = 2+2";
            galgo::Parameter<_TYPE, NBIT> par1({ (_TYPE)1.5, (_TYPE)3, 3 }); // an initial value can be added inside the initializer list after the upper bound
            galgo::Parameter<_TYPE, NBIT> par2({ (_TYPE)1.5, (_TYPE)3, 3 });

            config.Objective = SumSameAsPrdObjective<_TYPE>::Objective;
            galgo::GeneticAlgorithm<_TYPE> ga(config, par1, par2);
            ga.run();
        }

        {
            std::cout << std::endl;
            std::cout << "Rosenbrock function";
            galgo::Parameter<_TYPE, NBIT > par1({ (_TYPE)-2.0,(_TYPE)2.0 });
            galgo::Parameter<_TYPE, NBIT > par2({ (_TYPE)-2.0,(_TYPE)2.0 });
           
            config.Objective = RosenbrockObjective<_TYPE>::Objective;
            galgo::GeneticAlgorithm<_TYPE> ga(config, par1, par2);
            ga.run();
        }

        {
            std::cout << std::endl;
            std::cout << "Ackley function";
            galgo::Parameter<_TYPE, NBIT > par1({ (_TYPE)-4.0,(_TYPE)5.0 });
            galgo::Parameter<_TYPE, NBIT > par2({ (_TYPE)-4.0,(_TYPE)5.0 });

            config.Objective = AckleyObjective<_TYPE>::Objective;
            galgo::GeneticAlgorithm<_TYPE> ga(config, par1, par2);
            ga.run();
        }

        {
            std::cout << std::endl;
            std::cout << "Rastrigin function";
            galgo::Parameter<_TYPE, NBIT > par1({ (_TYPE)-4.0,(_TYPE)5.0 });
            galgo::Parameter<_TYPE, NBIT > par2({ (_TYPE)-4.0,(_TYPE)5.0 });
            galgo::Parameter<_TYPE, NBIT > par3({ (_TYPE)-4.0,(_TYPE)5.0 });

            config.Objective = rastriginObjective<_TYPE>::Objective;
            galgo::GeneticAlgorithm<_TYPE> ga(config, par1, par2, par3);
            ga.run();
        }

        {
            std::cout << std::endl;
            std::cout << "StyblinskiTang function Min = (-2.903534,...,--2.903534)";
            galgo::Parameter<_TYPE, NBIT > par1({ (_TYPE)-4.0,(_TYPE)4.0 });
            galgo::Parameter<_TYPE, NBIT > par2({ (_TYPE)-4.0,(_TYPE)4.0 });
            galgo::Parameter<_TYPE, NBIT > par3({ (_TYPE)-4.0,(_TYPE)4.0 });

            config.Objective = StyblinskiTangObjective<_TYPE>::Objective;
            galgo::GeneticAlgorithm<_TYPE> ga(config, par1, par2, par3);
            ga.run();
        }

        {
            std::cout << std::endl;
            std::cout << "Griewank function";
            galgo::Parameter<_TYPE, NBIT > par1({ (_TYPE)-4.0,(_TYPE)5.0 });
            galgo::Parameter<_TYPE, NBIT > par2({ (_TYPE)-4.0,(_TYPE)5.0 });
            galgo::Parameter<_TYPE, NBIT > par3({ (_TYPE)-4.0,(_TYPE)5.0 });

            config.Objective = GriewankObjective<_TYPE>::Objective;
            galgo::GeneticAlgorithm<_TYPE> ga(config, par1, par2, par3);
            ga.run();
        }
    }

    system("pause");
}

